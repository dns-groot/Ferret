namespace Authoritative
{
    using System.Diagnostics.CodeAnalysis;
    using ZenLib;
    using static ZenLib.Language;

    /// <summary>
    /// A query object.
    /// </summary>
    public class Query
    {
        /// <summary>
        /// The query name.
        /// </summary>
        public DomainName QName { get; set; }

        /// <summary>
        /// The query type.
        /// </summary>
        public RecordType QType { get; set; }

        /// <summary>
        /// Create a Zen query from a two tuple.
        /// </summary>
        /// <param name="name">The query name.</param>
        /// <param name="type">The query type.</param>
        /// <returns>A Zen Query.</returns>
        public static Zen<Query> Create(Zen<DomainName> name, Zen<RecordType> type)
        {
            return Language.Create<Query>(("QName", name), ("QType", type));
        }

        /// <summary>
        /// Convert the query to a string format.
        /// </summary>
        /// <returns>The string.</returns>
        [ExcludeFromCodeCoverage]
        public override string ToString()
        {
            return $"<{QName}, {QType}>";
        }
    }

    /// <summary>
    /// Extension Zen methods for Query.
    /// </summary>
    public static class QueryExtensions
    {
        /// <summary>
        /// Gets the name part of the query.
        /// </summary>
        /// <param name="q">The query.</param>
        /// <returns>The domain name of the query.</returns>
        public static Zen<DomainName> GetQName(this Zen<Query> q)
        {
            return q.GetField<Query, DomainName>("QName");
        }

        /// <summary>
        /// Gets the query type.
        /// </summary>
        /// <param name="q">The query.</param>
        /// <returns>The query type.</returns>
        public static Zen<RecordType> GetQType(this Zen<Query> q)
        {
            return q.GetField<Query, RecordType>("QType");
        }

        /// <summary>
        /// Whether a query is well-formed.
        /// </summary>
        /// <param name="q">The query.</param>
        /// <returns>A boolean.</returns>
        public static Zen<bool> IsValidQuery(this Zen<Query> q)
        {
            return And(
                Or(
                    q.GetQType() == RecordType.SOA,
                    q.GetQType() == RecordType.NS,
                    q.GetQType() == RecordType.CNAME,
                    q.GetQType() == RecordType.DNAME,
                    q.GetQType() == RecordType.A,
                    q.GetQType() == RecordType.AAAA,
                    q.GetQType() == RecordType.TXT),
                Not(q.GetQName().GetValue().IsEmpty()));
        }
    }
}
