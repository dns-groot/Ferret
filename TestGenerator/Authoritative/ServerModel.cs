namespace Authoritative
{
    using System.Collections.Generic;
    using System.Linq;
    using ZenLib;
    using static ZenLib.Language;

    /// <summary>
    /// Class representing the model for DNS authoritative server.
    /// </summary>
    public sealed class ServerModel
    {
        /// <summary>
        ///     Helper function to calculate the maximum of a list.
        /// </summary>
        /// <param name="numbers">The list of numbers.</param>
        /// <param name="maxSoFar">The maximum calculated so far.</param>
        /// <returns>The maximum number in the list.</returns>
        private static Zen<ushort> MaxofListHelper(Zen<IList<ushort>> numbers, Zen<ushort> maxSoFar)
        {
            return numbers.Case(
                empty: maxSoFar,
                cons: (hd, tl) => If(hd > maxSoFar, MaxofListHelper(tl, hd), MaxofListHelper(tl, maxSoFar)));
        }

        /// <summary>
        ///     Computes the maximum of a list.
        /// </summary>
        /// <param name="numbers">The list of numbers.</param>
        /// <returns>The maximum number in the list.</returns>
        public static Zen<ushort> MaxofList(Zen<IList<ushort>> numbers)
        {
            return MaxofListHelper(numbers, 0);
        }

        /// <summary>
        ///     Computes the maximal records with respect to the query (&lt;𝑞,𝑧) using 𝑟1 &lt;𝑞,𝑧 𝑟2 = Rank(𝑟1, 𝑞, 𝑧) ◁ Rank(𝑟2, 𝑞, 𝑧). (Equation 8).
        /// </summary>
        /// <param name="z">The zone.</param>
        /// <param name="q">The query.</param>
        /// <returns>The maximal records for the query.</returns>
        public static Zen<IList<ResourceRecord>> GetRelevantRRs(Zen<Query> q, Zen<Zone> z)
        {
            Zen<IList<ResourceRecord>> relevantRecords = z.GetRecords().Where(r => Or(Utils.IsPrefix(r.GetRName(), q.GetQName()), Utils.IsDomainWildcardMatch(q.GetQName(), r.GetRName())));
            Zen<DomainName> zoneDomain = z.GetRecords().Where(r => r.GetRType() == RecordType.SOA).At(0).Value().GetRName();
            Zen<IList<ResourceRecord>> nsRelevantRecords = relevantRecords.Where(r => And(r.GetRType() == RecordType.NS, r.GetRName() != zoneDomain));
            Zen<IList<ushort>> maximalMatches = relevantRecords.Select(r => Utils.MaximalPrefixMatch(r.GetRName(), q.GetQName()));
            Zen<IList<ResourceRecord>> maxMaximalMatches = relevantRecords.Where(r => Utils.MaximalPrefixMatch(r.GetRName(), q.GetQName()) == MaxofList(maximalMatches));
            Zen<IList<ResourceRecord>> wildcardRecords = maxMaximalMatches.Where(r => Utils.IsDomainWildcardMatch(q.GetQName(), r.GetRName()));

            return If(
                relevantRecords.IsEmpty(),
                new List<ResourceRecord> { },
                If(
                    nsRelevantRecords.IsEmpty(),
                    If(
                        wildcardRecords.IsEmpty(),
                        maxMaximalMatches,
                        wildcardRecords),
                    nsRelevantRecords));
        }

        /// <summary>
        ///   Evaluates the query against the zone.
        /// </summary>
        /// <param name="z">The zone.</param>
        /// <param name="q">The query.</param>
        /// <returns>The response for the query.</returns>
        public static Zen<Option<Response>> ServerLookup(Zen<Query> q, Zen<Zone> z)
        {
            return If(
                And(z.IsValidZoneForRRLookup(), q.IsValidQuery()),
                If(
                    Utils.IsPrefix(z.GetRecords().Where(r => r.GetRType() == RecordType.SOA).At(0).Value().GetRName(), q.GetQName()),
                    // N (𝑍, 𝑞) = {𝑧} (Here, there is only one zone file, so 𝑍 = {𝑧})
                    Some(RRLookup(GetRelevantRRs(q, z), q, z)),
                    // N(𝑍, 𝑞) = ∅
                    Some(Response.Create(Tag.REFUSED, new List<ResourceRecord>(), Null<Query>()))),
                Null<Response>());
        }

        private static Zen<Response> Rewrite(Zen<IList<ResourceRecord>> relevantRRs, Zen<Query> q)
        {
            var dnameRecord = relevantRRs.Where(r => r.GetRType() == RecordType.DNAME);
            var d = dnameRecord.At(0).Value().GetRData().GetValue().Append(q.GetQName().GetValue().SplitAt(dnameRecord.At(0).Value().GetRName().GetValue().Length() - 1).Item2());
            var synCname = ResourceRecord.Create(q.GetQName(), RecordType.CNAME, DomainName.Create(d));
            return Response.Create(Tag.DQR, dnameRecord.AddBack(synCname), Some(Query.Create(DomainName.Create(d), q.GetQType())));
        }

        /// <summary>
        ///   Constructs a response (answer) using the DNS resolution process given in RFC 6672 §3.2.
        /// </summary>
        /// <param name="relevantRecords">The maximal records for the query.</param>
        /// <param name="q">The query.</param>
        /// <param name="z">The zone.</param>
        /// <returns>The response for the query.</returns>
        public static Zen<Response> RRLookup(Zen<IList<ResourceRecord>> relevantRecords, Zen<Query> q, Zen<Zone> z)
        {
            // 𝑇 = {ty(𝑟) | 𝑟 ∈ 𝑅}
            Zen<IList<RecordType>> types = relevantRecords.Select(r => r.GetRType());

            return If(
                relevantRecords.At(0).Value().GetRName() == q.GetQName(),
                // dn(𝑅) = dn(𝑞)
                ExactMatch(relevantRecords, q, z),
                If(
                    Utils.IsDomainWildcardMatch(q.GetQName(), relevantRecords.At(0).Value().GetRName()),
                    // dn(𝑞) ∈∗ dn(𝑅)
                    WildcardMatch(relevantRecords, q, z),
                    If(
                        types.Any(t => t == RecordType.DNAME),
                        // DNAME ∈ 𝑇
                        Rewrite(relevantRecords, q),
                        If(
                            And(types.Any(t => t == RecordType.NS), Not(types.Any(t => t == RecordType.SOA))),
                            // DNAME ∉ 𝑇 , NS ∈ 𝑇 , SOA ∉ 𝑇
                            Response.Create(Tag.PRE, Delegation(relevantRecords, z), Null<Query>()),
                            // otherwise
                            Response.Create(Tag.PNX, new List<ResourceRecord>(), Null<Query>())))));
        }

        private static Zen<IList<ResourceRecord>> Delegation(Zen<IList<ResourceRecord>> relevantRecords, Zen<Zone> z)
        {
            var nsRecords = relevantRecords.Where(r => r.GetRType() == RecordType.NS);
            var glueRecords = z.GetRecords().Where(r => And(
                Or(
                    r.GetRType() == RecordType.A,
                    r.GetRType() == RecordType.AAAA),
                nsRecords.Any(ns => ns.GetRData() == r.GetRName())));
            return nsRecords.Append(glueRecords);
        }

        /// <summary>
        ///  Implements the sub-case of relevant records’ domain name matching exactly the query.
        /// </summary>
        /// <param name="relevantRecords">The maximal records for the query.</param>
        /// <param name="q">The query.</param>
        /// <param name="z">The zone.</param>
        /// <returns>The response for the query.</returns>
        public static Zen<Response> ExactMatch(Zen<IList<ResourceRecord>> relevantRecords, Zen<Query> q, Zen<Zone> z)
        {
            // 𝑇 = {ty(𝑟) | 𝑟 ∈ 𝑅}
            Zen<IList<RecordType>> types = relevantRecords.Select(r => r.GetRType());

            // Authoritative(𝑇) = NS ∉ 𝑇 ∨ SOA ∈ 𝑇
            Zen<bool> authoritative = Or(
                types.Where(t => t == RecordType.NS).IsEmpty(),
                Not(types.Where(t => t == RecordType.SOA).IsEmpty()));

            return If(
                authoritative,
                If(
                    types.Where(t => t == q.GetQType()).IsEmpty(),
                    If(
                        types.Where(t => t == RecordType.CNAME).IsEmpty(),
                        // otherwise
                        Response.Create(Tag.EAE, new List<ResourceRecord>(), Null<Query>()),
                        // Authoritative(𝑇), ty(𝑞) ∉ 𝑇 , CNAME ∈ 𝑇 , 𝑅 = {𝑟}
                        Response.Create(Tag.EAQ, relevantRecords, Some(Query.Create(relevantRecords.At(0).Value().GetRData(), q.GetQType())))),
                    // Authoritative(𝑇), ty(𝑞) ∈ 𝑇
                    Response.Create(Tag.EAA, relevantRecords.Where(r => r.GetRType() == q.GetQType()), Null<Query>())),
                // ¬Authoritative(𝑇 )
                Response.Create(Tag.ERE, Delegation(relevantRecords, z), Null<Query>()));
        }

        private static Zen<IList<ResourceRecord>> RecordSynthesis(Zen<IList<ResourceRecord>> records, Zen<DomainName> d)
        {
            return records.Select(r => ResourceRecord.Create(d, r.GetRType(), r.GetRData()));
        }

        /// <summary>
        ///  Implements the sub-case of query matching the wildcard relevant records.
        /// </summary>
        /// <param name="relevantRecords">The maximal records for the query.</param>
        /// <param name="q">The query.</param>
        /// <param name="z">The zone.</param>
        /// <returns>The response for the query.</returns>
        public static Zen<Response> WildcardMatch(Zen<IList<ResourceRecord>> relevantRecords, Zen<Query> q, Zen<Zone> z)
        {
            // 𝑇 = {ty(𝑟) | 𝑟 ∈ 𝑅}
            Zen<IList<RecordType>> types = relevantRecords.Select(r => r.GetRType());
            return If(
                types.Where(t => t == q.GetQType()).IsEmpty(),
                If(
                    types.Where(t => t == RecordType.CNAME).IsEmpty(),
                    // otherwise
                    Response.Create(Tag.WEA, new List<ResourceRecord>(), Null<Query>()),
                    // ty(𝑞) ∉ 𝑇 , CNAME ∈ 𝑇 , 𝑅 = {𝑟}
                    Response.Create(Tag.WQR, RecordSynthesis(relevantRecords, q.GetQName()), Some(Query.Create(relevantRecords.At(0).Value().GetRData(), q.GetQType())))),
                // ty(𝑞) ∈ 𝑇
                Response.Create(Tag.WSA, RecordSynthesis(relevantRecords.Where(r => r.GetRType() == q.GetQType()), q.GetQName()), Null<Query>()));
        }
    }
}
