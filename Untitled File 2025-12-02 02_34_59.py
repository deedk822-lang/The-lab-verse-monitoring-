-- Agent Workflow DevKit - SQL Schema v1.0
-- Complete database schema for managing durable AI agent workflows
-- Date: 2025-12-02

CREATE DATABASE IF NOT EXISTS agent_workflow_devkit;
USE agent_workflow_devkit;

-- Workflow Definitions Table
CREATE TABLE IF NOT EXISTS workflow_definitions (
  workflow_id STRING PRIMARY KEY,
    workflow_name STRING NOT NULL,
      description STRING,
        workflow_type STRING,
          status STRING DEFAULT 'ACTIVE',
            created_by STRING,
              created_at TIMESTAMP DEFAULT current_timestamp()
              );

              -- Workflow Executions Table
              CREATE TABLE IF NOT EXISTS workflow_executions (
                execution_id STRING PRIMARY KEY,
                  workflow_id STRING NOT NULL,
                    execution_status STRING DEFAULT 'PENDING',
                      start_time TIMESTAMP DEFAULT current_timestamp(),
                        end_time TIMESTAMP,
                          total_duration_ms LONG,
                            created_by STRING,
                              environment STRING,
                                FOREIGN KEY (workflow_id) REFERENCES workflow_definitions(workflow_id)
                                );

                                -- Workflow Steps Table
                                CREATE TABLE IF NOT EXISTS workflow_steps (
                                  step_id STRING PRIMARY KEY,
                                    workflow_id STRING NOT NULL,
                                      step_name STRING NOT NULL,
                                        step_type STRING,
                                          step_order INT,
                                            max_retries INT DEFAULT 3,
                                              retry_delay_ms INT DEFAULT 1000,
                                                timeout_ms INT DEFAULT 30000,
                                                  FOREIGN KEY (workflow_id) REFERENCES workflow_definitions(workflow_id)
                                                  );

                                                  -- Step Executions Table
                                                  CREATE TABLE IF NOT EXISTS step_executions (
                                                    step_execution_id STRING PRIMARY KEY,
                                                      execution_id STRING NOT NULL,
                                                        step_id STRING NOT NULL,
                                                          step_status STRING DEFAULT 'PENDING',
                                                            start_time TIMESTAMP,
                                                              end_time TIMESTAMP,
                                                                duration_ms LONG,
                                                                  retry_count INT DEFAULT 0,
                                                                    error_message STRING,
                                                                      FOREIGN KEY (execution_id) REFERENCES workflow_executions(execution_id),
                                                                        FOREIGN KEY (step_id) REFERENCES workflow_steps(step_id)
                                                                        );

                                                                        -- Workflow State Checkpoints Table
                                                                        CREATE TABLE IF NOT EXISTS workflow_state_checkpoints (
                                                                          checkpoint_id STRING PRIMARY KEY,
                                                                            execution_id STRING NOT NULL,
                                                                              checkpoint_name STRING NOT NULL,
                                                                                checkpoint_timestamp TIMESTAMP DEFAULT current_timestamp(),
                                                                                  state_data STRING,
                                                                                    checkpoint_type STRING,
                                                                                      FOREIGN KEY (execution_id) REFERENCES workflow_executions(execution_id)
                                                                                      );

                                                                                      -- Performance Metrics Table
                                                                                      CREATE TABLE IF NOT EXISTS workflow_metrics (
                                                                                        metric_id STRING PRIMARY KEY,
                                                                                          execution_id STRING NOT NULL,
                                                                                            metric_name STRING,
                                                                                              metric_value DOUBLE,
                                                                                                metric_type STRING,
                                                                                                  recorded_at TIMESTAMP DEFAULT current_timestamp(),
                                                                                                    FOREIGN KEY (execution_id) REFERENCES workflow_executions(execution_id)
                                                                                                    );

                                                                                                    -- Agent Tasks Table
                                                                                                    CREATE TABLE IF NOT EXISTS agent_tasks (
                                                                                                      task_id STRING PRIMARY KEY,
                                                                                                        execution_id STRING NOT NULL,
                                                                                                          task_description STRING,
                                                                                                            task_type STRING,
                                                                                                              agent_backend STRING,
                                                                                                                task_status STRING DEFAULT 'PENDING',
                                                                                                                  created_at TIMESTAMP DEFAULT current_timestamp(),
                                                                                                                    completed_at TIMESTAMP,
                                                                                                                      task_result STRING,
                                                                                                                        FOREIGN KEY (execution_id) REFERENCES workflow_executions(execution_id)
                                                                                                                        );

                                                                                                                        -- Debug Traces Table
                                                                                                                        CREATE TABLE IF NOT EXISTS debug_traces (
                                                                                                                          trace_id STRING PRIMARY KEY,
                                                                                                                            execution_id STRING NOT NULL,
                                                                                                                              trace_timestamp TIMESTAMP DEFAULT current_timestamp(),
                                                                                                                                trace_level STRING,
                                                                                                                                  trace_message STRING,
                                                                                                                                    trace_context STRING,
                                                                                                                                      FOREIGN KEY (execution_id) REFERENCES workflow_executions(execution_id)
                                                                                                                                      );

                                                                                                                                      -- Analytics Views
                                                                                                                                      CREATE OR REPLACE VIEW workflow_execution_summary AS
                                                                                                                                      SELECT we.execution_id, wd.workflow_name, we.execution_status,
                                                                                                                                             we.start_time, we.end_time, we.total_duration_ms,
                                                                                                                                                    COUNT(DISTINCT se.step_execution_id) as total_steps,
                                                                                                                                                           SUM(CASE WHEN se.step_status = 'SUCCESS' THEN 1 ELSE 0 END) as successful_steps
                                                                                                                                                           FROM workflow_executions we
                                                                                                                                                           JOIN workflow_definitions wd ON we.workflow_id = wd.workflow_id
                                                                                                                                                           LEFT JOIN step_executions se ON we.execution_id = se.execution_id
                                                                                                                                                           GROUP BY we.execution_id, wd.workflow_name, we.execution_status, we.start_time, we.end_time, we.total_duration_ms;

                                                                                                                                                           CREATE OR REPLACE VIEW workflow_performance_metrics AS
                                                                                                                                                           SELECT wd.workflow_name, COUNT(we.execution_id) as total_executions,
                                                                                                                                                                  AVG(we.total_duration_ms) as avg_duration_ms,
                                                                                                                                                                         SUM(CASE WHEN we.execution_status = 'SUCCESS' THEN 1 ELSE 0 END) as successful_executions,
                                                                                                                                                                                ROUND(100.0 * SUM(CASE WHEN we.execution_status = 'SUCCESS' THEN 1 ELSE 0 END) / COUNT(we.execution_id), 2) as success_rate_percent
                                                                                                                                                                                FROM workflow_definitions wd
                                                                                                                                                                                LEFT JOIN workflow_executions we ON wd.workflow_id = we.workflow_id
                                                                                                                                                                                GROUP BY wd.workflow_name;

                                                                                                                                                                                -- Indexes for Performance
                                                                                                                                                                                CREATE INDEX IF NOT EXISTS idx_we_status ON workflow_executions(execution_status);
                                                                                                                                                                                CREATE INDEX IF NOT EXISTS idx_se_status ON step_executions(step_status);
                                                                                                                                                                                CREATE INDEX IF NOT EXISTS idx_at_type ON agent_tasks(task_type);
                                                                                                                                                                                CREATE INDEX IF NOT EXISTS idx_dt_timestamp ON debug_traces(trace_timestamp);

                                                                                                                                                                                -- Schema Creation Complete
                                                                                                                                                                                SELECT 'Agent Workflow DevKit Schema Created Successfully' as status,
                                                                                                                                                                                       current_timestamp() as created_at, 'v1.0' as version;we