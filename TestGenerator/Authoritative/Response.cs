namespace Authoritative
{
    using System.Collections.Generic;
    using System.Diagnostics.CodeAnalysis;
    using System.Linq;
    using ZenLib;
    using static ZenLib.Language;

    /// <summary>
    /// Answer tag to indicate type of answer.
    /// </summary>
    public enum Tag
    {
        /// <summary>
        /// ExactMatch Authoritative Answer.
        /// </summary>
        E1,

        /// <summary>
        /// ExactMatch Authoritative Query rewrite.
        /// </summary>
        E2,

        /// <summary>
        /// ExactMatch Authoritative Empty answer.
        /// </summary>
        E3,

        /// <summary>
        /// ExactMatch REference.
        /// </summary>
        E4,

        /// <summary>
        /// Wildcard Synthesized Answer.
        /// </summary>
        W1,

        /// <summary>
        /// Wildcard Query Rewrite.
        /// </summary>
        W2,

        /// <summary>
        /// Wildcard Empty Answer.
        /// </summary>
        W3,

        /// <summary>
        /// DNAME Query Rewrite.
        /// </summary>
        D1,

        /// <summary>
        /// Prefix REference.
        /// </summary>
        R1,

        /// <summary>
        /// Prefix Non-existent.
        /// </summary>
        R2,

        /// <summary>
        /// Refused.
        /// </summary>
        REFUSED,

        /// <summary>
        /// Server failure.
        /// </summary>
        SERVFAIL,
    }

    /// <summary>
    /// A Response object.
    /// </summary>
    public sealed class Response
    {
        /// <summary>
        /// The response tag.
        /// </summary>
        public Tag ResTag { get; set; }

        /// <summary>
        /// The response data.
        /// </summary>
        public IList<ResourceRecord> ResRecords { get; set; }

        /// <summary>
        /// The rewritten query if the tag is ANSQ.
        /// </summary>
        public Option<Query> RewrittenQuery { get; set; }

        /// <summary>
        /// Create a Zen Response.
        /// </summary>
        /// <param name="tag">The response tag.</param>
        /// <param name="records">The pertinent resource records.</param>
        /// <param name="query">Any rewritten query.</param>
        /// <returns>A zen response.</returns>
        public static Zen<Response> Create(Zen<Tag> tag, Zen<IList<ResourceRecord>> records, Zen<Option<Query>> query)
        {
            return Language.Create<Response>(
                ("ResTag", tag),
                ("ResRecords", records),
                ("RewrittenQuery", query));
        }

        /// <summary>
        /// Convert the response to a string format.
        /// </summary>
        /// <returns>The string.</returns>
        [ExcludeFromCodeCoverage]
        public override string ToString()
        {
            var records = string.Join("\n", ResRecords);
            return $"Tag:\n\t{ResTag}\nRecords:\n\t{records}\nNew Query:\n\t{RewrittenQuery}";
        }
    }

    /// <summary>
    /// Response Zen extension methods.
    /// </summary>
    public static class ResponseExtensions
    {
        /// <summary>
        /// Gets the type of the answer.
        /// </summary>
        /// <param name="res">The response.</param>
        /// <returns>The tag.</returns>
        public static Zen<Tag> GetResTag(this Zen<Response> res) => res.GetField<Response, Tag>("ResTag");

        /// <summary>
        /// Gets the resource records holding pertinent information for a query.
        /// </summary>
        /// <param name="res">The response.</param>
        /// <returns>The resource records.</returns>
        public static Zen<IList<ResourceRecord>> GetResRecords(this Zen<Response> res) => res.GetField<Response, IList<ResourceRecord>>("ResRecords");

        /// <summary>
        /// Gets the new query if the response is of rewrite tag.
        /// </summary>
        /// <param name="res">The response.</param>
        /// <returns>An optinal new query.</returns>
        public static Zen<Option<Query>> GetRewrittenQuery(this Zen<Response> res) => res.GetField<Response, Option<Query>>("RewrittenQuery");

        /// <summary>
        /// Whether a response is well-formed.
        /// </summary>
        /// <param name="res">The response.</param>
        /// <returns>A boolean.</returns>
        public static Zen<bool> IsValidResponse(this Zen<Response> res)
        {
            IList<Zen<bool>> predicates = new List<Zen<bool>>();
            predicates.Add(
                Or(
                    res.GetResTag() == Tag.E1,
                    res.GetResTag() == Tag.E2,
                    res.GetResTag() == Tag.E3,
                    res.GetResTag() == Tag.E4,
                    res.GetResTag() == Tag.W1,
                    res.GetResTag() == Tag.W2,
                    res.GetResTag() == Tag.W3,
                    res.GetResTag() == Tag.D1,
                    res.GetResTag() == Tag.R1,
                    res.GetResTag() == Tag.R2,
                    res.GetResTag() == Tag.SERVFAIL,
                    res.GetResTag() == Tag.REFUSED));

            // If the tag is ANSQ (E2, W2, D1) then there has to be a valid rewritten query.
            predicates.Add(Implies(Or(res.GetResTag() == Tag.E2, res.GetResTag() == Tag.W2, res.GetResTag() == Tag.D1), And(res.GetRewrittenQuery().HasValue(), res.GetRewrittenQuery().Value().IsValidQuery())));

            // If the tag is not ANSQ then the rewritten query has to be empty.
            predicates.Add(Implies(And(res.GetResTag() != Tag.E2, res.GetResTag() != Tag.W2, res.GetResTag() != Tag.D1), Not(res.GetRewrittenQuery().HasValue())));

            // If the tag is NX or SERVFAIL or REFUSED then the records set should be empty.
            predicates.Add(Implies(
                Or(
                    res.GetResTag() == Tag.R2,
                    res.GetResTag() == Tag.SERVFAIL,
                    res.GetResTag() == Tag.REFUSED),
                res.GetResRecords().IsEmpty()));

            // If the tag is REF or ANSQ then the records set should be non-empty.
            predicates.Add(Implies(
               Or(
                   res.GetResTag() == Tag.E4,
                   res.GetResTag() == Tag.R1,
                   res.GetResTag() == Tag.E2,
                   res.GetResTag() == Tag.W2,
                   res.GetResTag() == Tag.D1),
               Not(res.GetResRecords().IsEmpty())));

            return predicates.Aggregate((a, b) => And(a, b));
        }
    }
}
