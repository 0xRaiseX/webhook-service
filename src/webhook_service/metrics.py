from prometheus_client import Counter, Histogram

delivery_success = Counter("delivery_success_total", "Successful deliveries")
delivery_retry = Counter("delivery_retry_total", "Retries for deliveries")
delivery_dead = Counter("delivery_dead_total", "Dead deliveries")
delivery_latency = Histogram("delivery_latency_seconds", "Webhook delivery latency")

