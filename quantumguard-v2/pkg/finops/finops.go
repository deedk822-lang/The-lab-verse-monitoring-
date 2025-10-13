package finops

import "context"

type Tagger struct{}

func MustTagger(ctx context.Context, s string) *Tagger {
	return &Tagger{}
}

type ReasoningEvent struct {
	Reasoner string
	Cost     float64
	TenantID string
}

func (t *Tagger) EmitUsage(ctx context.Context, event ReasoningEvent) {}