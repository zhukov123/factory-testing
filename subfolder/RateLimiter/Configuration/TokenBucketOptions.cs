namespace RateLimiter.Configuration;

public sealed record TokenBucketOptions
{
    public int Capacity { get; init; } = 100;

    public double TokensPerInterval { get; init; } = 1;

    public TimeSpan RefillInterval { get; init; } = TimeSpan.FromSeconds(1);

    public TokenBucketOptions()
    {
    }

    public TokenBucketOptions(int capacity, double tokensPerInterval, TimeSpan refillInterval)
    {
        Capacity = capacity;
        TokensPerInterval = tokensPerInterval;
        RefillInterval = refillInterval;
        Validate();
    }

    public void Validate()
    {
        if (Capacity <= 0)
        {
            throw new ArgumentOutOfRangeException(nameof(Capacity), "Capacity must be greater than zero.");
        }

        if (TokensPerInterval <= 0)
        {
            throw new ArgumentOutOfRangeException(nameof(TokensPerInterval), "Tokens per interval must be greater than zero.");
        }

        if (RefillInterval <= TimeSpan.Zero)
        {
            throw new ArgumentOutOfRangeException(nameof(RefillInterval), "Refill interval must be greater than zero.");
        }
    }
}
