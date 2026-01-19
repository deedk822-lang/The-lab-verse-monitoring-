// src/config/EnterpriseConfig.ts
import { z } from 'zod';
import fs from 'fs';
import path from 'path';

// Schema definitions with enterprise-grade validation
export const RiskThresholdsSchema = z.object({
  low: z.number().min(0).max(1),
  medium: z.number().min(0).max(1),
  high: z.number().min(0).max(1),
  critical: z.number().min(0).max(1)
});
export type RiskThresholds = z.infer<typeof RiskThresholdsSchema>;

export const EscalationRulesSchema = z.record(
  z.string(),
  z.union([
    z.literal("immediate"),
    z.literal("within_15_minutes"),
    z.literal("within_30_minutes"),
    z.literal("within_1_hour"),
    z.literal("within_2_hours"),
    z.literal("within_4_hours")
  ])
);
export type EscalationRules = z.infer<typeof EscalationRulesSchema>;

export const AuditLogSchema = z.object({
  enabled: z.boolean(),
  retention_days: z.number().int().positive(),
  encryption_at_rest: z.boolean(),
  include_decision_rationale: z.boolean()
});
export type AuditLog = z.infer<typeof AuditLogSchema>;

export const RollbackPolicySchema = z.object({
  on_failure: z.boolean(),
  grace_period_minutes: z.number().int().nonnegative(),
  max_retries: z.number().int().nonnegative(),
  exponential_backoff: z.boolean(),
  require_human_approval_after_retries: z.boolean()
});
export type RollbackPolicy = z.infer<typeof RollbackPolicySchema>;

export const ResourceLimitsSchema = z.object({
  cpu: z.string(),
  memory: z.string(),
  max_disk_usage: z.string(),
  max_network_bandwidth: z.string()
});
export type ResourceLimits = z.infer<typeof ResourceLimitsSchema>;

export const ModelValidationSchema = z.object({
  minimum_confidence: z.number().min(0).max(1),
  drift_detection_enabled: z.boolean(),
  drift_threshold: z.number().min(0).max(1),
  retrain_trigger: z.string(),
  validation_dataset_required: z.boolean()
});
export type ModelValidation = z.infer<typeof ModelValidationSchema>;

export const CompetitiveIntelligenceSchema = z.object({
  benchmarking_enabled: z.boolean(),
  competitor_monitoring: z.boolean(),
  superiority_tracking: z.boolean(),
  market_position_analysis: z.boolean()
});
export type CompetitiveIntelligence = z.infer<typeof CompetitiveIntelligenceSchema>;

export const BusinessImpactTrackingSchema = z.object({
  revenue_anomaly_tracking: z.boolean(),
  cost_optimization_tracking: z.boolean(),
  customer_churn_prediction: z.boolean(),
  roi_calculation_enabled: z.boolean()
});
export type BusinessImpactTracking = z.infer<typeof BusinessImpactTrackingSchema>;

export const ExplainabilitySchema = z.object({
  shap_analysis_enabled: z.boolean(),
  lime_analysis_enabled: z.boolean(),
  feature_importance_tracking: z.boolean(),
  counterfactual_explanations: z.boolean(),
  business_language_explanations: z.boolean()
});
export type Explainability = z.infer<typeof ExplainabilitySchema>;

export const MultiCloudSchema = z.object({
  enabled: z.boolean(),
  providers: z.array(z.string()).nonempty(),
  edge_deployment: z.boolean(),
  cross_region_sync: z.boolean(),
  failover_automation: z.boolean()
});
export type MultiCloud = z.infer<typeof MultiCloudSchema>;

export const MobileIntegrationSchema = z.object({
  push_notifications: z.boolean(),
  offline_sync: z.boolean(),
  biometric_auth: z.boolean(),
  real_time_alerts: z.boolean(),
  competitive_scorecard: z.boolean()
});
export type MobileIntegration = z.infer<typeof MobileIntegrationSchema>;

export const ChaosEngineeringSchema = z.object({
  enabled: z.boolean(),
  intensity_levels: z.array(z.number().min(0).max(1)),
  scenarios: z.array(z.string()),
  safety_checks: z.boolean(),
  automatic_rollback: z.boolean()
});
export type ChaosEngineering = z.infer<typeof ChaosEngineeringSchema>;

export const PerformanceOptimizationSchema = z.object({
  caching_enabled: z.boolean(),
  cache_ttl_seconds: z.number().int().positive(),
  parallel_processing: z.boolean(),
  batch_size_optimization: z.boolean(),
  tail_latency_optimization: z.boolean()
});
export type PerformanceOptimization = z.infer<typeof PerformanceOptimizationSchema>;

export const SecurityHardeningSchema = z.object({
  encryption_in_transit: z.boolean(),
  encryption_at_rest: z.boolean(),
  api_rate_limiting: z.boolean(),
  input_validation: z.boolean(),
  output_sanitization: z.boolean(),
  audit_trail: z.boolean()
});
export type SecurityHardening = z.infer<typeof SecurityHardeningSchema>;

export const CompetitorDifferentiationSchema = z.object({
  accuracy_advantage: z.number(),
  prediction_horizon_advantage: z.number(),
  false_positive_advantage: z.number(),
  cost_optimization_advantage: z.number(),
  multi_cloud_advantage: z.number()
});
export type CompetitorDifferentiation = z.infer<typeof CompetitorDifferentiationSchema>;

export const GoToMarketSchema = z.object({
  demo_environment_enabled: z.boolean(),
  competitive_challenges: z.boolean(),
  sales_enablement: z.boolean(),
  whitepaper_generation: z.boolean(),
  case_study_automation: z.boolean()
});
export type GoToMarket = z.infer<typeof GoToMarketSchema>;

export const EnterpriseConfigSchema = z.object({
  version: z.string(),
  human_oversight_mode: z.enum(['manual', 'collaborative', 'automated']),
  auto_execution_threshold: z.number().min(0).max(1),
  human_checkin_interval_hours: z.number().int().positive(),
  max_concurrent_tasks: z.number().int().positive(),

  risk_thresholds: RiskThresholdsSchema,
  escalation_rules: EscalationRulesSchema,
  audit_log: AuditLogSchema,
  rollback_policy: RollbackPolicySchema,
  resource_limits: ResourceLimitsSchema,
  model_validation: ModelValidationSchema,
  competitive_intelligence: CompetitiveIntelligenceSchema,
  business_impact_tracking: BusinessImpactTrackingSchema,
  explainability: ExplainabilitySchema,
  multi_cloud_deployment: MultiCloudSchema,
  mobile_integration: MobileIntegrationSchema,
  chaos_engineering: ChaosEngineeringSchema,
  performance_optimization: PerformanceOptimizationSchema,
  security_hardening: SecurityHardeningSchema,
  competitor_differentiation: CompetitorDifferentiationSchema,
  go_to_market: GoToMarketSchema
});

export type EnterpriseConfig = z.infer<typeof EnterpriseConfigSchema>;

export class EnterpriseConfigLoader {
  private static _instance: EnterpriseConfigLoader | null = null;
  private config!: EnterpriseConfig;

  private constructor() {
    this.loadConfig();
  }

  public static getInstance(): EnterpriseConfigLoader {
    if (this._instance === null) {
      this._instance = new EnterpriseConfigLoader();
    }
    return this._instance;
  }

  private loadConfig(): void {
    const cfgPath = path.resolve(__dirname, '../../../../config/enterprise-config.json');
    let raw: string;

    try {
      raw = fs.readFileSync(cfgPath, 'utf8');
    } catch (err) {
      console.error('❌ Error reading enterprise-config.json:', err);
      throw err;
    }

    let parsed: unknown;
    try {
      parsed = JSON.parse(raw);
    } catch (err) {
      console.error('❌ Invalid JSON in enterprise-config.json:', err);
      throw err;
    }

    try {
      const validated = EnterpriseConfigSchema.parse(parsed);
      this.config = validated;
      console.log(`✅ Enterprise config loaded. Version: ${validated.version}`);
      console.log(`🏢 Enterprise Features: Multi-cloud=${validated.multi_cloud_deployment.enabled}, Chaos=${validated.chaos_engineering.enabled}, Mobile=${validated.mobile_integration.push_notifications}`);
    } catch (err) {
      console.error('❌ Enterprise config validation failed:', err);
      throw err;
    }
  }

  public getConfig(): EnterpriseConfig {
    return JSON.parse(JSON.stringify(this.config));
  }

  public reload(): void {
    console.log('🔄 Reloading enterprise configuration...');
    this.loadConfig();
  }

  public getCompetitiveAdvantages(): CompetitorDifferentiation {
    return this.config.competitor_differentiation;
  }

  public isEnterpriseFeatureEnabled(feature: keyof EnterpriseConfig): boolean {
    const value = this.config[feature];
    if (typeof value === 'boolean') {
      return value;
    }
    if (typeof value === 'object' && value !== null && 'enabled' in value && typeof value.enabled === 'boolean') {
        return value.enabled;
    }
    return false;
  }
}