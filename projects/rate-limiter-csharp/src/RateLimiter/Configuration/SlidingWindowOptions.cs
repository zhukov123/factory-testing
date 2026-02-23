namespace RateLimiter.Configuration;

public sealed record SlidingWindowOptions
{
    public int MaxRequests { get; init; } = 100;

    public TimeSpan Window { get; init; } = TimeSpan.FromSeconds(1);

    public SlidingWindowOptions()
    {
    }

    public SlidingWindowOptions(int maxRequests, TimeSpan window)
    {
        MaxRequests = maxRequests;
        Window = window;
        Validate();
    }

    public void Validate()
    {
        if (MaxRequests <= 0)
        {
            throw new ArgumentOutOfRangeException(nameof(MaxRequests), "Max requests must be greater than zero.");
        }

        if (Window <= TimeSpan.Zero)
        {
            throw new ArgumentOutOfRangeException(nameof(Window), "Window must be greater than zero.");
        }
    }
}
