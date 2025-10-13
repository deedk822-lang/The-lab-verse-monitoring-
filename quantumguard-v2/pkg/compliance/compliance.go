package compliance

import (
	"context"
	"github.com/your-org/quantumguard-v2/pkg/reasoners"
)

type Engine struct{}

func (e *Engine) ValidateAction(ctx context.Context, action reasoners.Action) error {
	return nil
}