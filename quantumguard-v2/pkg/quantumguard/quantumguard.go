package quantumguard

import (
	"context"
	"net/http"

	"github.com/your-org/quantumguard-v2/pkg/arf"
	"github.com/your-org/quantumguard-v2/pkg/finops"
	"github.com/your-org/quantumguard-v2/pkg/reasoners"
	"github.com/your-org/quantumguard-v2/pkg/compliance"
	"github.com/your-org/quantumguard-v2/pkg/telemetry"
)

// QuantumGuard plugs into The-Lap-Verse-Monitoring without breaking existing routes
type QuantumGuard struct {
	ARF *arf.AutonomicReasoningFabric
}

func MustBuild(ctx context.Context) *QuantumGuard {
	// Re-use existing FinOps tagger from The-Lap-Verse-Monitoring
	cost := finops.MustTagger(ctx, "quantumguard-core")
	// Re-use existing telemetry tracer
	tracer := telemetry.MustTracer(ctx, "quantumguard-v2")

	arf := arf.MustBuild(ctx, cost, tracer)

	return &QuantumGuard{ARF: arf}
}

// HandleAnomaly plugs into your existing anomaly detection loop
func (qg *QuantumGuard) HandleAnomaly(metrics reasoners.SystemMetrics) error {
	return qg.ARF.AutoRemediation.Execute(context.Background(), metrics)
}