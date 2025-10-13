package telemetry

import "context"

type Tracer struct{}

func MustTracer(ctx context.Context, s string) *Tracer {
	return &Tracer{}
}