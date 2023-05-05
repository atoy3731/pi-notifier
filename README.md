# Pi Notifier

Silly-simple tool to send a notification to Slack when RPis are available. Leverages RSS from https://rpilocator.com/

## Configuration Environment Variables

| Environment Variables | Description | Required | Default |
|---|---|---|---|
| SLACK_TOKEN | Slack API Token to publish messages to channel | Yes |  |
| SLACK_CHANNEL | Slack channel to publish to | Yes | #pi-notify |
| CHECK_INTERVAL | Interval in Seconds to Check | No | 60 |
| FILTERS | Comma-Separated List of Filters (against the Summary) | No |  |
| COUNTRY | Country Filter | No |  |
| PROCESS_INIT | Whether to process the initial list of RSS entries or just new entries | No | true |

## Installation

### Creating a Slack token

See [here](https://api.slack.com/tutorials/tracks/getting-a-token) for getting a token.

### Kubernetes

1. Check the values in [values.yaml](chart/values.yaml).
2. Use helm to install, with your configurations, similar to:
    ```bash
    helm install -n pi-notifier --create-namespace --set config.slackToken=abcdef12345 --set config.slackChannel=#example-channel pi-notifier chart/
    ```
3. Check logs:
    ```bash
    kubectl get logs -n pi-notifier -l app.kubernetes.io/name=pi-notifier
    ```
   
### Docker

1. Update the `docker-compose.yaml` file with your settings.
2. Run `docker-compose up -d`.
3. Validate logs with `docker logs -f pi-notifier`.

