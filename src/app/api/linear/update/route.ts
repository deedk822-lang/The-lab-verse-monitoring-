import { NextRequest, NextResponse } from 'next/server';

export const runtime = 'edge';

const LINEAR_API_URL = 'https://api.linear.app/graphql';

const linearRequest = async <T>(
  query: string,
  variables: Record<string, unknown>,
): Promise<T> => {
  const response = await fetch(LINEAR_API_URL, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${process.env.LINEAR_API_KEY ?? ''}`,
    },
    body: JSON.stringify({ query, variables }),
  });

  const payload = (await response.json()) as {
    data?: T;
    errors?: Array<{ message: string }>;
  };

  if (!response.ok || payload.errors?.length) {
    const message = payload.errors?.[0]?.message || 'Linear API error';
    throw new Error(message);
  }

  if (!payload.data) {
    throw new Error('Missing Linear response');
  }

  return payload.data;
};

export async function POST(req: NextRequest) {
  const { task_id, status, comment } = (await req.json()) as {
    task_id: string;
    status?: string;
    comment?: string;
  };

  try {
    if (!process.env.LINEAR_API_KEY) {
      return NextResponse.json(
        { error: 'Missing LINEAR_API_KEY' },
        { status: 500 },
      );
    }

    if (!task_id) {
      return NextResponse.json(
        { error: 'Missing task_id' },
        { status: 400 },
      );
    }

    if (status) {
      const issueData = await linearRequest<{
        issue: {
          team: {
            states: { nodes: Array<{ id: string; name: string }> };
          } | null;
        } | null;
      }>(
        `query IssueStates($id: String!) {
          issue(id: $id) {
            team {
              states {
                nodes {
                  id
                  name
                }
              }
            }
          }
        }`,
        { id: task_id },
      );

      const targetState = issueData.issue?.team?.states.nodes.find(
        (state) => state.name === status,
      );

      if (targetState) {
        await linearRequest(
          `mutation UpdateIssue($id: String!, $stateId: String!) {
            issueUpdate(id: $id, input: { stateId: $stateId }) {
              success
            }
          }`,
          { id: task_id, stateId: targetState.id },
        );
      }
    }

    if (comment) {
      await linearRequest(
        `mutation AddComment($issueId: String!, $body: String!) {
          commentCreate(input: { issueId: $issueId, body: $body }) {
            comment {
              id
            }
          }
        }`,
        {
          issueId: task_id,
          body: `🤖 **Kimi K2.5 Agent Update**: ${comment}`,
        },
      );
    }

    return NextResponse.json({ success: true });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unknown error';
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
