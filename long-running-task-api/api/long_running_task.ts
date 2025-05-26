import type { VercelRequest, VercelResponse } from '@vercel/node';

function sleep(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function sendWebhookUpdate(
  webhookUrl: string,
  webhookHeaders: Record<string, string>,
  event: object
) {
  try {
    await fetch(webhookUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...webhookHeaders,
      },
      body: JSON.stringify(event),
    });
  } catch (err) {
    console.error('Failed to send webhook update:', err);
  }
}

export default async function handler(req: VercelRequest, res: VercelResponse) {
  if (req.method !== 'POST') {
    res.status(405).json({ error: 'Method not allowed' });
    return;
  }

  try {
    const { task_name, duration_minutes, webhook_url__, webhook_headers__ } = req.body;
    if (!task_name || !duration_minutes) {
      res.status(400).json({ error: 'Missing required fields' });
      return;
    }

    const taskId = `task_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    const totalSteps = Math.ceil((duration_minutes * 60) / 5);
    let progress = 0;

    for (let step = 1; step <= totalSteps; step++) {
      progress = Math.round((step / totalSteps) * 100);
      if (webhook_url__) {
        const event = {
          type: 'status-update',
          metadata: {
            progress,
            estimatedTimeRemaining: `${(totalSteps - step) * 5}s`,
          },
          status: {
            message: {
              parts: [
                {
                  type: 'text',
                  text: `Task '${task_name}' is ${progress}% complete.`,
                },
              ],
            },
            state: step === totalSteps ? 'COMPLETED' : 'PROCESSING',
            timestamp: new Date().toISOString(),
          },
        };
        await sendWebhookUpdate(webhook_url__, webhook_headers__ || {}, event);
      }
      if (step < totalSteps) {
        await sleep(5000);
      }
    }

    // Final completion event
    if (webhook_url__) {
      const event = {
        type: 'status-update',
        metadata: {
          progress: 100,
          estimatedTimeRemaining: '0s',
        },
        status: {
          message: {
            parts: [
              {
                type: 'text',
                text: `Task '${task_name}' completed!`,
              },
            ],
          },
          state: 'COMPLETED',
          timestamp: new Date().toISOString(),
        },
      };
      await sendWebhookUpdate(webhook_url__, webhook_headers__ || {}, event);
    }

    res.status(200).json({ message: `Task '${task_name}' started.`, taskId });
  } catch (err) {
    console.error('Error in long_running_task:', err);
    res.status(500).json({ error: 'Internal server error' });
  }
}