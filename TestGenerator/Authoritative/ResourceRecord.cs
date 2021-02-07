namespace Authoritative
{
    using System.Collections.Generic;
    using System.Diagnostics.CodeAnalysis;
    using System.Linq;
    using ZenLib;
    using static ZenLib.Language;

    /// <summary>
    /// Record types.
    /// </summary>
    public enum RecordType
    {
        /// <summary>
        /// Start of authority data.
        /// </summary>
        SOA,

        /// <summary>
        /// Nameserver referral.
        /// </summary>
        NS,

        /// <summary>
        /// Ipv4 address.
        /// </summary>
        A,

        /// <summary>
        /// Record alias.
        /// </summary>
        CNAME,

        /// <summary>
        /// Domain redirection.
        /// </summary>
        DNAME,

        /// <summary>
        /// IPv6 address.
        /// </summary>
        AAAA,

        /// <summary>
        /// Text data.
        /// </summary>
        TXT,

        /// <summary>
        /// Empty data.
        /// </summary>
        N,
    }

    /// <summary>
    /// A Resource Record object.
    /// </summary>
    public sealed class ResourceRecord
    {
        /// <summary>
        /// The record name.
        /// </summary>
        public DomainName RName { get; set; }

        /// <summary>
        /// The record tye.
        /// </summary>
        public RecordType RType { get; set; }

        /// <summary>
        /// The record data.
        /// </summary>
        public DomainName RData { get; set; }

        /// <summary>
        /// Create a Zen RR from a three tuple.
        /// </summary>
        /// <param name="name">The record name.</param>
        /// <param name="type">The record type.</param>
        /// <param name="rData">The record data.</param>
        /// <returns>A Zen RR.</returns>
        public static Zen<ResourceRecord> Create(
            Zen<DomainName> name,
            Zen<RecordType> type,
            Zen<DomainName> rData)
        {
            return Language.Create<ResourceRecord>(
                ("RName", name),
                ("RType", type),
                ("RData", rData));
        }

        /// <summary>
        ///     Equality for domain names.
        /// </summary>
        /// <param name="other">The other domain name.</param>
        /// <returns>True or false.</returns>
        public bool Equals(ResourceRecord other)
        {
            return RName.Equals(other.RName) && RType == other.RType && RData.Equals(other.RData);
        }

        /// <summary>
        /// Convert the resource record to a string format.
        /// </summary>
        /// <returns>The string.</returns>
        [ExcludeFromCodeCoverage]
        public override string ToString()
        {
            return $"{RName}\t{RType}\t{RData}";
        }
    }

    /// <summary>
    /// Resource record Zen extension methods.
    /// </summary>
    public static class ResourceRecordExtensions
    {
        /// <summary>
        /// Gets the name of the resource record.
        /// </summary>
        /// <param name="rr">The resource record.</param>
        /// <returns>The domain name of the record.</returns>
        public static Zen<DomainName> GetRName(this Zen<ResourceRecord> rr) => rr.GetField<ResourceRecord, DomainName>("RName");

        /// <summary>
        /// Gets the type of the resource record.
        /// </summary>
        /// <param name="rr">The resource record.</param>
        /// <returns>The record type.</returns>
        public static Zen<RecordType> GetRType(this Zen<ResourceRecord> rr) => rr.GetField<ResourceRecord, RecordType>("RType");

        /// <summary>
        /// Gets the rdata of the resource record.
        /// </summary>
        /// <param name="rr">The resource record.</param>
        /// <returns>The answer(rdata) of the record.</returns>
        public static Zen<DomainName> GetRData(this Zen<ResourceRecord> rr) => rr.GetField<ResourceRecord, DomainName>("RData");

        /// <summary>
        /// Checks whether a record is a wildcard record.
        /// </summary>
        /// <param name="rr">The resource record.</param>
        /// <returns>A boolean.</returns>
        public static Zen<bool> IsWildcardRecord(this Zen<ResourceRecord> rr) => rr.GetRName().IsWildcardDomain();

        /// <summary>
        /// Whether a record is well-formed.
        /// </summary>
        /// <param name="rr">The resource record.</param>
        /// <returns>A boolean.</returns>
        public static Zen<bool> IsValidRecord(this Zen<ResourceRecord> rr)
        {
            IList<Zen<bool>> predicates = new List<Zen<bool>>();
            predicates.Add(
                Or(
                    rr.GetRType() == RecordType.SOA,
                    rr.GetRType() == RecordType.NS,
                    rr.GetRType() == RecordType.CNAME,
                    rr.GetRType() == RecordType.DNAME,
                    rr.GetRType() == RecordType.A,
                    rr.GetRType() == RecordType.AAAA,
                    rr.GetRType() == RecordType.TXT,
                    rr.GetRType() == RecordType.N));

            // Name should be non-empty.
            predicates.Add(Not(rr.GetRName().GetValue().IsEmpty()));

            // If the type is A or SOA or AAAA or TXT then the rdata is to be left empty.
            predicates.Add(
                Implies(
                    Or(
                        rr.GetRType() == RecordType.SOA,
                        rr.GetRType() == RecordType.A,
                        rr.GetRType() == RecordType.AAAA,
                        rr.GetRType() == RecordType.TXT,
                        rr.GetRType() == RecordType.N),
                    rr.GetRData().GetValue().IsEmpty()));

            // If the type is NS, CNAME, DNAME then the rdata should be non-empty. (Condition 4)
            predicates.Add(
                Implies(
                    Or(
                        rr.GetRType() == RecordType.NS,
                        rr.GetRType() == RecordType.CNAME,
                        rr.GetRType() == RecordType.DNAME),
                    Not(rr.GetRData().GetValue().IsEmpty())));

            // Wildcard domain names can not have a SOA or a DNAME or an NS record. (Condition 11)
            predicates.Add(Implies(rr.IsWildcardRecord(), And(rr.GetRType() != RecordType.SOA, rr.GetRType() != RecordType.DNAME, rr.GetRType() != RecordType.NS)));
            return predicates.Aggregate((a, b) => And(a, b));
        }
    }
}
