"""Advanced pricing calculation engine.

Python port of the Java AdvancedPricingCalculationServiceImpl (990 lines).

Core algorithm:
  - Pre-load grid prices, wholesale prices, market allocation, base prices for a given month
  - For each package type (flat-rate vs timed), linearly search the smallest price difference
    that yields >= MIN_PROFIT_MARGIN per kWh
  - Select the package that maximizes customer savings (tie-break: max profit)
  - Fallback: zero price difference with manual-adjustment recommendation
"""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

from sqlalchemy.orm import Session

from app.models.price import (
    BasePrice,
    GridPrice,
    MarketAllocationPrice,
    WholesalePrice,
)

logger = logging.getLogger(__name__)

# ─── Constants (from Java AdvancedPricingCalculationServiceImpl) ───────────

MAX_PRICE_DIFFERENCE = Decimal("0.03984")
MIN_PRICE_DIFFERENCE = Decimal("-0.03984")
MIN_PROFIT_MARGIN = Decimal("0.0005")
SEARCH_STEP = Decimal("0.001")
GOOD_PROFIT_MARGIN = Decimal("0.008")

# Time period coefficients
COEFF_PEAK = Decimal("1.92")     # 尖峰
COEFF_HIGH = Decimal("1.60")     # 高峰
COEFF_NORMAL = Decimal("1.00")   # 平时
COEFF_VALLEY = Decimal("0.45")   # 低谷

PEAK_MONTHS = {1, 7, 8, 12}


# ─── Time-period utilities (port of PriceUtils.java) ───────────────────────

def calculate_time_period(hour: int, month: int) -> int:
    """Return time period code: 1=PEAK(尖), 2=HIGH(峰), 3=NORMAL(平), 4=VALLEY(谷)."""
    valley_hours = {0, 1, 2, 3, 4, 5, 6, 11, 12}
    peak_hours = {18, 19}
    high_hours = {8, 9, 17, 18, 19, 20, 21, 22}

    if hour in valley_hours:
        return 4
    if month in PEAK_MONTHS and hour in peak_hours:
        return 1
    if hour in high_hours:
        return 2
    return 3


def get_price_coefficient(period: int) -> Decimal:
    """Get multiplier for a time period."""
    return {1: COEFF_PEAK, 2: COEFF_HIGH, 3: COEFF_NORMAL, 4: COEFF_VALLEY}.get(period, COEFF_NORMAL)


def _round2(value: Decimal) -> Decimal:
    """Round to 2 decimal places."""
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _round4(value: Decimal) -> Decimal:
    """Round to 4 decimal places."""
    return value.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


def _round6(value: Decimal) -> Decimal:
    """Round to 6 decimal places."""
    return value.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)


# ─── Pre-calculated data container ─────────────────────────────────────────

@dataclass
class PreCalculatedData:
    """Container for all price data needed by the pricing engine."""
    grid_prices: dict[int, Decimal] = field(default_factory=dict)          # hour → price
    wholesale_prices: dict[int, Decimal] = field(default_factory=dict)     # hour → price
    base_prices: dict[int, Decimal] = field(default_factory=dict)          # hour → price
    market_allocation_price: Decimal = Decimal("0")
    flat_rate_base_price: Decimal = Decimal("0")
    total_consumption: Decimal = Decimal("0")
    usage_month: str = ""


# ─── Data loaders ──────────────────────────────────────────────────────────

def _parse_year_month(usage_month: str) -> tuple[int, int]:
    """Parse 'YYYY-MM' string into (year, month)."""
    parts = usage_month.split("-")
    return int(parts[0]), int(parts[1])


def _load_grid_prices(db: Session, usage_month: str) -> dict[int, Decimal]:
    """Load grid prices and expand to 24-hour using time-period coefficients."""
    rows = (
        db.query(GridPrice)
        .filter(
            GridPrice.year_month == usage_month,
            GridPrice.deleted_at.is_(None),
        )
        .all()
    )
    if not rows:
        raise ValueError(f"未找到 {usage_month} 的电网价格数据")

    # Build period→price map from GridPrice rows
    period_prices: dict[int, Decimal] = {}
    for row in rows:
        if row.time_period is not None and row.price is not None:
            period_prices[row.time_period] = row.price

    _, month = _parse_year_month(usage_month)
    hourly: dict[int, Decimal] = {}
    for hour in range(24):
        period = calculate_time_period(hour, month)
        hourly[hour] = period_prices.get(period) or period_prices.get(3) or Decimal("0")

    return hourly


def _load_wholesale_prices(db: Session, usage_month: str) -> dict[int, Decimal]:
    """Load 24-hour wholesale prices for the month."""
    rows = (
        db.query(WholesalePrice)
        .filter(
            WholesalePrice.price_month == usage_month,
            WholesalePrice.deleted_at.is_(None),
        )
        .all()
    )
    hourly: dict[int, Decimal] = {}
    for row in rows:
        if row.hour_index is not None and row.wholesale_price is not None:
            hourly[row.hour_index] = row.wholesale_price

    if len(hourly) < 24:
        raise ValueError(f"批发价格数据不完整，{usage_month} 仅找到 {len(hourly)} 小时的数据")

    return hourly


def _load_market_allocation(db: Session, usage_month: str) -> Decimal:
    """Load market allocation price for the month."""
    row = (
        db.query(MarketAllocationPrice)
        .filter(
            MarketAllocationPrice.year_month == usage_month,
            MarketAllocationPrice.deleted_at.is_(None),
            MarketAllocationPrice.status == 0,  # 0=enabled, 1=disabled
        )
        .first()
    )
    if not row or row.allocation_price is None:
        return Decimal("0")
    return row.allocation_price


def _load_base_prices(db: Session, usage_month: str) -> dict[int, Decimal]:
    """Load 24-hour base (分时基准) prices for the month."""
    year, month = _parse_year_month(usage_month)
    # Try to match by date range within the month
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1)
    else:
        end_date = date(year, month + 1, 1)

    rows = (
        db.query(BasePrice)
        .filter(
            BasePrice.price_date >= start_date,
            BasePrice.price_date < end_date,
            BasePrice.deleted_at.is_(None),
        )
        .all()
    )
    hourly: dict[int, Decimal] = {}
    for row in rows:
        if row.hour_index is not None and row.price is not None:
            hourly[row.hour_index] = row.price

    if len(hourly) < 24:
        raise ValueError(f"分时基准价格数据不完整，{usage_month} 仅找到 {len(hourly)} 小时的数据")

    return hourly


def load_pre_calculated_data(
    db: Session, usage_month: str, hourly_consumption: list[Decimal]
) -> PreCalculatedData:
    """Load all price data needed for pricing calculations."""
    grid = _load_grid_prices(db, usage_month)
    wholesale = _load_wholesale_prices(db, usage_month)
    allocation = _load_market_allocation(db, usage_month)
    base = _load_base_prices(db, usage_month)

    # Flat-rate base price = mean of all non-zero base prices
    non_zero = [v for v in base.values() if v and v > 0]
    flat_rate = sum(non_zero, Decimal("0")) / Decimal(len(non_zero)) if non_zero else Decimal("0")
    flat_rate = _round6(flat_rate)

    total_consumption = sum(hourly_consumption, Decimal("0"))

    return PreCalculatedData(
        grid_prices=grid,
        wholesale_prices=wholesale,
        base_prices=base,
        market_allocation_price=allocation,
        flat_rate_base_price=flat_rate,
        total_consumption=total_consumption,
        usage_month=usage_month,
    )


# ─── Core pricing formula ──────────────────────────────────────────────────

@dataclass
class PackagePricingResult:
    """Result of pricing calculation for a single package type."""
    package_type: int
    price_difference: Decimal
    hourly_prices: dict[int, Decimal] = field(default_factory=dict)
    total_electricity_fee: Decimal = Decimal("0")
    total_consumption: Decimal = Decimal("0")
    average_price: Decimal = Decimal("0")
    savings: Decimal = Decimal("0")
    savings_rate: Decimal = Decimal("0")
    profit: Decimal = Decimal("0")
    profit_rate: Decimal = Decimal("0")
    grid_total_fee: Decimal = Decimal("0")
    wholesale_total_cost: Decimal = Decimal("0")
    market_allocation_fee: Decimal = Decimal("0")
    successful: bool = True
    error_message: str = ""


def calculate_package_pricing(
    pre_data: PreCalculatedData,
    hourly_consumption: list[Decimal],
    price_difference: Decimal,
    package_type: int,
) -> PackagePricingResult:
    """
    Core per-package pricing formula.

    Given a price difference and package type, compute:
      - 24-hour customer prices
      - total electricity fee, grid fee, wholesale cost
      - savings (vs grid), profit (revenue - wholesale - allocation)
      - rates and averages
    """
    _, month = _parse_year_month(pre_data.usage_month)

    # 1. Compute 24-hour customer prices
    hourly_prices: dict[int, Decimal] = {}
    if package_type == 1:
        # Flat-rate: normalPrice * coefficient
        normal_price = pre_data.flat_rate_base_price + price_difference
        for hour in range(24):
            period = calculate_time_period(hour, month)
            coeff = get_price_coefficient(period)
            hourly_prices[hour] = _round6(normal_price * coeff)
    elif package_type == 2:
        # Timed: base price + difference per hour
        for hour in range(24):
            base = pre_data.base_prices.get(hour, Decimal("0"))
            hourly_prices[hour] = _round6(base + price_difference)
    else:
        return PackagePricingResult(
            package_type=package_type,
            price_difference=price_difference,
            successful=False,
            error_message=f"未知套餐类型: {package_type}",
        )

    # 2. Validate price difference range
    if price_difference < MIN_PRICE_DIFFERENCE or price_difference > MAX_PRICE_DIFFERENCE:
        return PackagePricingResult(
            package_type=package_type,
            price_difference=price_difference,
            successful=False,
            error_message="价差超出允许范围",
        )

    # 3. Aggregate hourly fees
    total_electricity_fee = Decimal("0")
    grid_total_fee = Decimal("0")
    wholesale_total_cost = Decimal("0")

    for hour in range(24):
        consumption = hourly_consumption[hour] if hour < len(hourly_consumption) else Decimal("0")
        total_electricity_fee += hourly_prices[hour] * consumption
        grid_total_fee += pre_data.grid_prices.get(hour, Decimal("0")) * consumption
        wholesale_total_cost += pre_data.wholesale_prices.get(hour, Decimal("0")) * consumption

    # 4. Revenue, market allocation, savings, profit
    total_consumption = pre_data.total_consumption
    market_allocation_fee = total_consumption * pre_data.market_allocation_price
    savings = grid_total_fee - total_electricity_fee
    profit = total_electricity_fee - wholesale_total_cost - market_allocation_fee

    # 5. Ratios & averages
    savings_rate = (savings / grid_total_fee * 100) if grid_total_fee != 0 else Decimal("0")
    profit_rate = (profit / total_electricity_fee * 100) if total_electricity_fee != 0 else Decimal("0")
    average_price = (total_electricity_fee / total_consumption) if total_consumption != 0 else Decimal("0")

    return PackagePricingResult(
        package_type=package_type,
        price_difference=price_difference,
        hourly_prices=hourly_prices,
        total_electricity_fee=_round2(total_electricity_fee),
        total_consumption=_round2(total_consumption),
        average_price=_round6(average_price),
        savings=_round2(savings),
        savings_rate=_round4(savings_rate),
        profit=_round2(profit),
        profit_rate=_round4(profit_rate),
        grid_total_fee=_round2(grid_total_fee),
        wholesale_total_cost=_round2(wholesale_total_cost),
        market_allocation_fee=_round2(market_allocation_fee),
        successful=True,
    )


# ─── Optimal price-difference search ───────────────────────────────────────

def _check_min_profit(result: PackagePricingResult) -> bool:
    """Check if profit per kWh meets minimum threshold."""
    if not result.successful or result.total_consumption == 0:
        return False
    return (result.profit / result.total_consumption) >= MIN_PROFIT_MARGIN


def _find_best_effort_price_difference(
    pre_data: PreCalculatedData,
    hourly_consumption: list[Decimal],
    package_type: int,
) -> Optional[Decimal]:
    """Fallback: find first price diff with any positive profit per kWh."""
    current = MIN_PRICE_DIFFERENCE
    while current <= MAX_PRICE_DIFFERENCE:
        result = calculate_package_pricing(pre_data, hourly_consumption, current, package_type)
        if result.successful and result.total_consumption > 0:
            if (result.profit / result.total_consumption) > 0:
                return current
        current += SEARCH_STEP
    return None


def find_optimal_price_difference(
    pre_data: PreCalculatedData,
    hourly_consumption: list[Decimal],
    package_type: int,
) -> Optional[Decimal]:
    """
    Linear search for the smallest price difference that yields >= MIN_PROFIT_MARGIN per kWh.
    Smaller price differences = greater customer savings (search ascending).
    """
    best: Optional[Decimal] = None
    current = MIN_PRICE_DIFFERENCE
    while current <= MAX_PRICE_DIFFERENCE:
        result = calculate_package_pricing(pre_data, hourly_consumption, current, package_type)
        if result.successful and result.total_consumption > 0:
            profit_per_kwh = result.profit / result.total_consumption
            if profit_per_kwh >= MIN_PROFIT_MARGIN:
                best = current
                break
        current += SEARCH_STEP

    if best is None:
        best = _find_best_effort_price_difference(pre_data, hourly_consumption, package_type)

    return best or Decimal("0")


# ─── Package selection ─────────────────────────────────────────────────────

def _select_better_package_by_score(
    timed: PackagePricingResult, flat_rate: PackagePricingResult
) -> PackagePricingResult:
    """Tie-breaker: maximize savings, then profit."""
    timed_savings_per = timed.savings / timed.total_consumption if timed.total_consumption else Decimal("0")
    flat_savings_per = flat_rate.savings / flat_rate.total_consumption if flat_rate.total_consumption else Decimal("0")

    if timed_savings_per > flat_savings_per:
        return timed
    if timed_savings_per < flat_savings_per:
        return flat_rate

    # Tie on savings → maximize profit
    timed_profit_per = timed.profit / timed.total_consumption if timed.total_consumption else Decimal("0")
    flat_profit_per = flat_rate.profit / flat_rate.total_consumption if flat_rate.total_consumption else Decimal("0")
    return timed if timed_profit_per >= flat_profit_per else flat_rate


def select_optimal_package(
    timed: Optional[PackagePricingResult],
    flat_rate: Optional[PackagePricingResult],
) -> Optional[PackagePricingResult]:
    """Multi-gate decision tree to pick the winning package."""
    if not timed and not flat_rate:
        return None
    if not timed:
        return flat_rate if (flat_rate.successful and _check_min_profit(flat_rate)) else None
    if not flat_rate:
        return timed if (timed.successful and _check_min_profit(timed)) else None
    if not timed.successful and not flat_rate.successful:
        return None
    if not timed.successful:
        return flat_rate if _check_min_profit(flat_rate) else None
    if not flat_rate.successful:
        return timed if _check_min_profit(timed) else None

    timed_ok = _check_min_profit(timed)
    flat_ok = _check_min_profit(flat_rate)

    if not timed_ok and not flat_ok:
        return None
    if not timed_ok:
        return flat_rate
    if not flat_ok:
        return timed

    return _select_better_package_by_score(timed, flat_rate)


# ─── Recommendation ────────────────────────────────────────────────────────

@dataclass
class OptimalPricingRecommendation:
    """Top-level recommendation containing both packages and the winner."""
    successful: bool = True
    recommended_package_type: int = 2  # default to timed
    optimal_price_difference: Decimal = Decimal("0")
    expected_savings: Decimal = Decimal("0")
    expected_savings_rate: Decimal = Decimal("0")
    expected_profit: Decimal = Decimal("0")
    expected_profit_rate: Decimal = Decimal("0")
    expected_monthly_fee: Decimal = Decimal("0")
    timed_package_result: Optional[PackagePricingResult] = None
    flat_rate_package_result: Optional[PackagePricingResult] = None
    recommendation_reason: str = ""
    price_difference_explanation: str = ""
    risk_assessment: str = ""
    error_message: str = ""


def _generate_recommendation_details(
    recommendation: OptimalPricingRecommendation,
    optimal: PackagePricingResult,
) -> None:
    """Populate human-readable fields on the recommendation."""
    savings_per_kwh = optimal.savings / optimal.total_consumption if optimal.total_consumption else Decimal("0")
    profit_per_kwh = optimal.profit / optimal.total_consumption if optimal.total_consumption else Decimal("0")

    package_name = "一口价套餐" if recommendation.recommended_package_type == 1 else "分时价套餐"
    recommendation.recommendation_reason = (
        f"{package_name}让客户省钱{_round6(savings_per_kwh)}元/度，"
        f"{'充分利用分时电价优势' if recommendation.recommended_package_type == 2 else '相比国网价格更有竞争力'}"
    )
    recommendation.price_difference_explanation = (
        f"推荐价差{recommendation.optimal_price_difference}元/度，"
        f"在保证公司利润({_round6(profit_per_kwh)}元/度)的前提下，让客户省钱最多"
    )

    if profit_per_kwh >= GOOD_PROFIT_MARGIN:
        recommendation.risk_assessment = "利润水平良好，业务风险可控"
    elif profit_per_kwh >= MIN_PROFIT_MARGIN:
        recommendation.risk_assessment = "利润水平适中，建议关注市场波动"
    else:
        recommendation.risk_assessment = "利润水平偏低，建议谨慎评估风险"


def _result_to_dict(result: Optional[PackagePricingResult]) -> Optional[dict]:
    """Convert PackagePricingResult to a JSON-serializable dict."""
    if not result:
        return None
    return {
        "packageType": result.package_type,
        "priceDifference": float(result.price_difference),
        "hourlyPrices": {str(h): float(p) for h, p in result.hourly_prices.items()},
        "totalElectricityFee": float(result.total_electricity_fee),
        "totalConsumption": float(result.total_consumption),
        "averagePrice": float(result.average_price),
        "savings": float(result.savings),
        "savingsRate": float(result.savings_rate),
        "profit": float(result.profit),
        "profitRate": float(result.profit_rate),
        "gridTotalFee": float(result.grid_total_fee),
        "wholesaleTotalCost": float(result.wholesale_total_cost),
        "marketAllocationFee": float(result.market_allocation_fee),
        "successful": result.successful,
        "errorMessage": result.error_message,
    }


# ─── Top-level orchestrator ────────────────────────────────────────────────

def calculate_optimal_pricing(
    db: Session,
    inquiry_id: int,
    usage_month: str,
    hourly_consumption: list[Decimal],
) -> OptimalPricingRecommendation:
    """
    Top-level pricing orchestrator.

    Loads data, runs parallel searches for both package types,
    selects the winner, and generates recommendation text.
    """
    pre_data = load_pre_calculated_data(db, usage_month, hourly_consumption)

    # Run both searches in parallel using ThreadPoolExecutor
    timed_diff: Optional[Decimal] = None
    flat_diff: Optional[Decimal] = None

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = {
            pool.submit(find_optimal_price_difference, pre_data, hourly_consumption, 2): "timed",
            pool.submit(find_optimal_price_difference, pre_data, hourly_consumption, 1): "flat",
        }
        for future in as_completed(futures):
            label = futures[future]
            try:
                result = future.result(timeout=15)
                if label == "timed":
                    timed_diff = result
                else:
                    flat_diff = result
            except Exception as e:
                logger.warning("Pricing search failed for %s: %s", label, e)

    # Compute per-package results for found diffs
    timed_result = (
        calculate_package_pricing(pre_data, hourly_consumption, timed_diff, 2)
        if timed_diff is not None
        else None
    )
    flat_rate_result = (
        calculate_package_pricing(pre_data, hourly_consumption, flat_diff, 1)
        if flat_diff is not None
        else None
    )

    # Pick the winner
    optimal = select_optimal_package(timed_result, flat_rate_result)

    if optimal is None or not optimal.successful:
        # Last-ditch fallback: zero price difference
        timed_zero = calculate_package_pricing(pre_data, hourly_consumption, Decimal("0"), 2)
        flat_zero = calculate_package_pricing(pre_data, hourly_consumption, Decimal("0"), 1)

        rec = OptimalPricingRecommendation(
            successful=True,
            recommended_package_type=2,
            optimal_price_difference=Decimal("0"),
            expected_savings=Decimal("0"),
            expected_savings_rate=Decimal("0"),
            expected_profit=timed_zero.profit if timed_zero.successful else Decimal("0"),
            expected_profit_rate=timed_zero.profit_rate if timed_zero.successful else Decimal("0"),
            expected_monthly_fee=timed_zero.total_electricity_fee if timed_zero.successful else Decimal("0"),
            timed_package_result=timed_zero,
            flat_rate_package_result=flat_zero,
            recommendation_reason=(
                f"系统无法找到满足最小利润要求的价差，已设置为0价差供您手动调整。"
                f"当前国网总电费: {_round2(timed_zero.grid_total_fee if timed_zero.successful else Decimal('0'))}元，"
                f"最小利润要求: 0.0005元/度。请根据实际情况在前端手动调整价差。"
            ),
            price_difference_explanation="价差为0，需要手动调整",
            risk_assessment="无法自动确定最优价差，建议人工评估",
        )
        return rec

    # Populate winner values
    used_diff = flat_diff if optimal.package_type == 1 else timed_diff

    rec = OptimalPricingRecommendation(
        successful=True,
        recommended_package_type=optimal.package_type,
        optimal_price_difference=used_diff or Decimal("0"),
        expected_savings=optimal.savings,
        expected_savings_rate=optimal.savings_rate,
        expected_profit=optimal.profit,
        expected_profit_rate=optimal.profit_rate,
        expected_monthly_fee=optimal.total_electricity_fee,
        timed_package_result=timed_result,
        flat_rate_package_result=flat_rate_result,
    )
    _generate_recommendation_details(rec, optimal)
    return rec


def recommendation_to_dict(rec: OptimalPricingRecommendation) -> dict:
    """Convert recommendation to JSON-serializable dict for API response."""
    return {
        "successful": rec.successful,
        "recommendedPackageType": rec.recommended_package_type,
        "optimalPriceDifference": float(rec.optimal_price_difference),
        "expectedSavings": float(rec.expected_savings),
        "expectedSavingsRate": float(rec.expected_savings_rate),
        "expectedProfit": float(rec.expected_profit),
        "expectedProfitRate": float(rec.expected_profit_rate),
        "expectedMonthlyFee": float(rec.expected_monthly_fee),
        "timedPackageResult": _result_to_dict(rec.timed_package_result),
        "flatRatePackageResult": _result_to_dict(rec.flat_rate_package_result),
        "recommendationReason": rec.recommendation_reason,
        "priceDifferenceExplanation": rec.price_difference_explanation,
        "riskAssessment": rec.risk_assessment,
        "errorMessage": rec.error_message,
    }


# ─── Dynamic pricing (what-if calculator) ──────────────────────────────────

def calculate_timed_package_pricing(
    db: Session, usage_month: str, price_difference: Decimal, hourly_consumption: list[Decimal]
) -> PackagePricingResult:
    """Calculate timed package pricing for a user-supplied price difference."""
    pre_data = load_pre_calculated_data(db, usage_month, hourly_consumption)
    return calculate_package_pricing(pre_data, hourly_consumption, price_difference, 2)


def calculate_flat_rate_package_pricing(
    db: Session, usage_month: str, price_difference: Decimal, hourly_consumption: list[Decimal]
) -> PackagePricingResult:
    """Calculate flat-rate package pricing for a user-supplied price difference."""
    pre_data = load_pre_calculated_data(db, usage_month, hourly_consumption)
    return calculate_package_pricing(pre_data, hourly_consumption, price_difference, 1)
