namespace RateLimiter;

public sealed record RateLimitHitEventArgs(string LimiterName, int RequestedTokens, DateTimeOffset Timestamp);
