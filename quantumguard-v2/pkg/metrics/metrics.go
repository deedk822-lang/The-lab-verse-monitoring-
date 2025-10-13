package metrics

import (
	"go.opentelemetry.io/otel/metric"
	"go.opentelemetry.io/otel/metric/noop"
)

var meterProvider = noop.NewMeterProvider()
var meter = meterProvider.Meter("quantumguard-v2")

var (
	RemediationCost, _ = meter.Float64Counter("lapverse_remediation.cost_usd",
		metric.WithDescription("Cost per auto-remediation action in USD"))
	RemediationSuccess, _ = meter.Int64Counter("lapverse_remediation.success_total",
		metric.WithDescription("Successful auto-remediation actions"))
)