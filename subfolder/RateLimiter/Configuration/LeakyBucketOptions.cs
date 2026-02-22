namespace RateLimiter.Configuration;

public sealed record LeakyBucketOptions
{
    public int Capacity { get; init; } = 100;

    public TimeSpan LeakInterval { get; init; } = TimeSpan.FromSeconds(1);

    public LeakyBucketOptions()
    {
    }

    public LeakyBucketOptions(int capacity, TimeSpan leakInterval)
    {
        Capacity = capacity;
        LeakInterval = leakInterval;
        Validate();
    }

    public void Validate()
    {
        if (Capacity <= 0)
        {
            throw new ArgumentOutOfRangeException(nameof(Capacity), "Capacity must be greater than zero.");
        }

        if (LeakInterval <= TimeSpan.Zero)
        {
            throw new ArgumentOutOfRangeException(nameof(LeakInterval), "Leak interval must be greater than zero.");
        }
    }
}
