namespace Authoritative
{
    using System.Collections.Generic;
    using ZenLib;
    using static ZenLib.Language;

    /// <summary>
    /// Commonly used functions.
    /// </summary>
    public static class Utils
    {
        /// <summary>
        ///     Checks if one domain is a prefix (≤) of the other.
        /// </summary>
        /// <param name="x">The domain to check if it is a prefix of the other.</param>
        /// <param name="y">The other domain.</param>
        /// <returns>True if x ≤ y or false.</returns>
        public static Zen<bool> IsPrefix(Zen<DomainName> x, Zen<DomainName> y)
        {
            return If(
                   y.GetValue().Length() < x.GetValue().Length(),
                   false,
                   x.GetValue().Case(
                        empty: Implies(true, true),
                        cons: (hd, tl) =>
                            If(hd == y.GetValue().At(0).Value(),
                                IsPrefix(DomainName.Create(tl), DomainName.Create(y.GetValue().SplitAt(0).Item2())),
                                false)));
        }

        /// <summary>
        ///   Helper function to calculate the maximum number of common labels.
        /// </summary>
        /// <param name="x">The first domain.</param>
        /// <param name="y">The second domain.</param>
        /// <param name="commonLength">Count of the matching labels so far.</param>
        /// <returns>Number of common prefix labels.</returns>
        private static Zen<ushort> MaximalPrefixMatchHelper(Zen<IList<byte>> x, Zen<IList<byte>> y, Zen<ushort> commonLength)
        {
            return x.Case(
               empty: commonLength,
               cons: (hd, tl) => If(
                   y.Length() == 0,
                   commonLength,
                   If(
                       hd == y.At(0).Value(),
                       MaximalPrefixMatchHelper(tl, y.SplitAt(0).Item2(), commonLength + 1),
                       commonLength)));
        }

        /// <summary>
        ///   Finds out the maximum number of labels common to both the domains. (max {𝑗 | x ≃𝑗 y}).
        /// </summary>
        /// <param name="x">The first domain.</param>
        /// <param name="y">The second domain.</param>
        /// <returns>Number of common prefix labels.</returns>
        public static Zen<ushort> MaximalPrefixMatch(Zen<DomainName> x, Zen<DomainName> y)
        {
            return MaximalPrefixMatchHelper(x.GetValue(), y.GetValue(), 0);
        }

        /// <summary>
        ///     Checks if a wildcard domain matches the other domain.
        ///     𝑑1 ∈∗ 𝑑2 = (|𝑑2 | ≤ |𝑑1 |) ∧ (𝑑1 ≃(|𝑑2 |−1) 𝑑2) ∧ 𝑑1 [ |𝑑2 | ] ≠ ∗ = 𝑑2 [ |𝑑2 | ].
        /// </summary>
        /// <param name="d1">The domain to check if it is matched by a wildcard domain.</param>
        /// <param name="d2">The potential wildcard domain.</param>
        /// <returns>A boolean.</returns>
        public static Zen<bool> IsDomainWildcardMatch(Zen<DomainName> d1, Zen<DomainName> d2)
        {
            return And(
                d2.GetValue().Length() <= d1.GetValue().Length(),
                d2.IsWildcardDomain(),
                d1.GetValue().At(d2.GetValue().Length() - 1).Value() != 1,
                MaximalPrefixMatch(d1, d2) == d2.GetValue().Length() - 1);
        }
    }
}
