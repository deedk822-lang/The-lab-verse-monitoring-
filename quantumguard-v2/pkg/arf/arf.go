package arf

import (
	"context"
	"github.com/your-org/quantumguard-v2/pkg/finops"
	"github.com/your-org/quantumguard-v2/pkg/telemetry"
)

type AutonomicReasoningFabric struct {
	AutoRemediation *AutoRemediation
}

func MustBuild(ctx context.Context, cost *finops.Tagger, tracer *telemetry.Tracer) *AutonomicReasoningFabric {
	return &AutonomicReasoningFabric{
		AutoRemediation: &AutoRemediation{},
	}
}