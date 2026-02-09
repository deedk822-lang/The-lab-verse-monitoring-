package reasoners

import "context"

type Pool struct{}

type SystemMetrics struct {
	ErrorRate float64
	TenantID  string
}

type Action struct{}

func (p *Pool) Solve(ctx context.Context, metrics SystemMetrics) Action {
	return Action{}
}