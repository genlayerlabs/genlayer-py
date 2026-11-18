import pytest

from genlayer_py.transactions.fees import (
    build_estimated_fees_options_from_simulation,
    observed_simulation_fee_usage,
    transaction_fee_estimate_from_studio_estimate,
)

FLOOR = 1_000_000

# Real Studio v0.123.0-rc.11 simulation (genlayer-py#119).
RC11_CONSUMED = 78_628_500_000_000
RC11_REPORT_TOTAL = 78_628_000_000_000
RC11_GENVM_EXECUTION = 78_852_500_000_000
RC11_EXPECTED_BUDGET = 94_623_000_000_000
RC11_DOUBLE_COUNTED_BUDGET = 188_707_800_000_000


def _policy(floor: int = FLOOR) -> dict:
    return {
        "enabled": True,
        "genPerTimeUnit": 10,
        "storageUnitPrice": 1,
        "receiptGasPrice": 1,
        "executionBudgetFloor": floor,
        "timeUnitOverlayBps": 0,
    }


def _rc11_simulation() -> dict:
    return {
        "feeAccounting": {
            "execution_fee_consumed": str(RC11_CONSUMED),
            "execution_fee_consumed_buckets": [78_628_000_000_000, 500_000_000],
        },
        "feeReport": {
            "totalEstimatedFee": str(RC11_REPORT_TOTAL),
            "chargeableExecution": {"totalExecution": str(RC11_CONSUMED)},
            "genvmBuckets": {"execution": str(RC11_GENVM_EXECUTION)},
        },
    }


def test_rc11_simulation_does_not_double_count_execution_fee():
    observed = observed_simulation_fee_usage(
        {"simulation": _rc11_simulation()}, _policy()
    )

    assert observed["recommendedExecutionBudgetPerRound"] == RC11_EXPECTED_BUDGET
    assert observed["recommendedExecutionBudgetPerRound"] != RC11_DOUBLE_COUNTED_BUDGET
    assert observed["executionFeeConsumed"] == RC11_CONSUMED
    assert observed["executionFeeReportTotal"] == RC11_REPORT_TOTAL
    assert observed["observedExecutionFee"] == RC11_CONSUMED
    assert observed["genvmExecutionRequired"] == RC11_GENVM_EXECUTION
    assert observed["observedExecutionBudget"] == RC11_GENVM_EXECUTION


def test_rc11_simulation_preset_uses_corrected_execution_budget():
    preset = build_estimated_fees_options_from_simulation(
        {"simulation": _rc11_simulation()}, _policy()
    )

    assert preset["estimateOptions"]["executionBudgetPerRound"] == RC11_EXPECTED_BUDGET


def test_rc11_studio_estimate_reports_corrected_observed_budget():
    simulation = _rc11_simulation()
    estimate = transaction_fee_estimate_from_studio_estimate(
        {
            "feeAccounting": simulation["feeAccounting"],
            "feeReport": simulation["feeReport"],
            "recommendedPreset": {
                "distribution": {
                    "leaderTimeunitsAllocation": "100",
                    "validatorTimeunitsAllocation": "200",
                    "appealRounds": "0",
                    "executionBudgetPerRound": str(RC11_EXPECTED_BUDGET),
                    "executionConsumed": "0",
                    "totalMessageFees": "0",
                    "rotations": ["0"],
                    "maxPriceGenPerTimeUnit": "10",
                    "storageFeeMaxGasPrice": "1",
                    "receiptFeeMaxGasPrice": "1",
                },
                "feeValue": "1",
            },
        },
        _policy(),
    )

    assert estimate is not None
    assert estimate["distribution"]["executionBudgetPerRound"] == (RC11_EXPECTED_BUDGET)
    assert estimate["observed"]["recommendedExecutionBudgetPerRound"] == (
        RC11_EXPECTED_BUDGET
    )


@pytest.mark.parametrize(
    ("accounting", "report", "observed_fee", "budget"),
    [
        pytest.param(
            {"execution_fee_consumed": "0"},
            {
                "totalEstimatedFee": "5000000",
                "chargeableExecution": {"totalExecution": "7000000"},
            },
            7_000_000,
            8_400_000,
            id="chargeable-total-when-consumed-zero",
        ),
        pytest.param(
            {"executionFeeConsumed": 0},
            {
                "total_estimated_fee": 5_000_000,
                "chargeable_execution": {"total_execution": 0},
            },
            5_000_000,
            6_000_000,
            id="report-total-when-consumed-and-chargeable-zero",
        ),
        pytest.param(
            {"execution_fee_consumed": "3000000"},
            {"totalEstimatedFee": "3000000"},
            3_000_000,
            3_600_000,
            id="genvm-buckets-absent",
        ),
        pytest.param(
            {"execution_fee_consumed": "0"},
            {
                "totalEstimatedFee": "0",
                "chargeableExecution": {"totalExecution": "0"},
                "genvmBuckets": {"execution": "0"},
            },
            0,
            0,
            id="all-zero",
        ),
        pytest.param(
            {"execution_fee_consumed": "100"},
            {
                "totalEstimatedFee": "100",
                "genvmBuckets": {"execution": "200"},
            },
            100,
            FLOOR,
            id="floor-dominates",
        ),
    ],
)
def test_observed_execution_fee_fallbacks(accounting, report, observed_fee, budget):
    observed = observed_simulation_fee_usage(
        {"simulation": {"feeAccounting": accounting, "feeReport": report}},
        _policy(),
    )

    assert observed["observedExecutionFee"] == observed_fee
    assert observed["recommendedExecutionBudgetPerRound"] == budget


def test_observed_execution_fee_reads_report_from_fee_accounting():
    observed = observed_simulation_fee_usage(
        {
            "simulation": {
                "feeAccounting": {
                    "execution_fee_consumed": str(RC11_CONSUMED),
                    "execution_fee_report": {
                        "totalEstimatedFee": str(RC11_REPORT_TOTAL),
                        "genvmBuckets": {"execution": str(RC11_GENVM_EXECUTION)},
                    },
                }
            }
        },
        _policy(),
    )

    assert observed["recommendedExecutionBudgetPerRound"] == RC11_EXPECTED_BUDGET
