using Microsoft.Extensions.DependencyInjection;

namespace RateLimiter;

public static class ServiceCollectionExtensions
{
    public static IServiceCollection AddRateLimiter<TLimiter>(this IServiceCollection services, Func<IServiceProvider, TLimiter> factory)
        where TLimiter : class, IAsyncRateLimiter
    {
        services.AddSingleton(factory);
        services.AddSingleton<IRateLimiter>(sp => sp.GetRequiredService<TLimiter>());
        services.AddSingleton<IAsyncRateLimiter>(sp => sp.GetRequiredService<TLimiter>());
        return services;
    }

    public static IServiceCollection AddTokenBucketLimiter(this IServiceCollection services, Configuration.TokenBucketOptions options, string? name = null)
        => services.AddRateLimiter<TokenBucketRateLimiter>(_ => new TokenBucketRateLimiter(options, name));

    public static IServiceCollection AddLeakyBucketLimiter(this IServiceCollection services, Configuration.LeakyBucketOptions options, string? name = null)
        => services.AddRateLimiter<LeakyBucketRateLimiter>(_ => new LeakyBucketRateLimiter(options, name));

    public static IServiceCollection AddFixedWindowLimiter(this IServiceCollection services, Configuration.FixedWindowOptions options, string? name = null)
        => services.AddRateLimiter<FixedWindowRateLimiter>(_ => new FixedWindowRateLimiter(options, name));

    public static IServiceCollection AddSlidingWindowLimiter(this IServiceCollection services, Configuration.SlidingWindowOptions options, string? name = null)
        => services.AddRateLimiter<SlidingWindowRateLimiter>(_ => new SlidingWindowRateLimiter(options, name));
}
