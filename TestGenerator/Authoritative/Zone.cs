namespace Authoritative
{
    using System.Collections.Generic;
    using System.Diagnostics.CodeAnalysis;
    using System.Linq;
    using ZenLib;
    using static ZenLib.Language;

    /// <summary>
    /// A zone object.
    /// </summary>
    public sealed class Zone
    {
        /// <summary>
        /// Resource Records in a zone.
        /// </summary>
        public IList<ResourceRecord> Records { get; set; }

        /// <summary>
        /// Create a Zen zone.
        /// </summary>
        /// <param name="records">The resource records.</param>
        /// <returns>A zen zone.</returns>
        public static Zen<Zone> Create(Zen<IList<ResourceRecord>> records)
        {
            return Language.Create<Zone>(("Records", records));
        }

        /// <summary>
        /// Convert the zone to a string format.
        /// </summary>
        /// <returns>The string.</returns>
        [ExcludeFromCodeCoverage]
        public override string ToString()
        {
            return string.Join("\n", Records);
        }
    }

    /// <summary>
    /// Zone utils.
    /// </summary>
    static class ZoneUtils
    {
        /// <summary>
        /// Checks whether there are any duplicate records in a zone.
        /// The checking is similar to running a double for loop.
        /// </summary>
        /// <param name="records">The records to check.</param>
        /// <param name="zoneRecords">The zone records.</param>
        /// <returns>True or false.</returns>
        public static Zen<bool> RecordUniqueness(Zen<IList<ResourceRecord>> records, Zen<IList<ResourceRecord>> zoneRecords)
        {
            return records.All(r => zoneRecords.Where(zr => zr == r).Length() == 1);
        }

        /// <summary>
        /// Checks whether there is more than a record if there is a CNAME record for a domain.
        /// </summary>
        /// <param name="cnameRecords">The cname records to check.</param>
        /// <param name="zoneRecords">Thezone records.</param>
        /// <returns>True or false.</returns>
        public static Zen<bool> SingleCname(Zen<IList<ResourceRecord>> cnameRecords, Zen<IList<ResourceRecord>> zoneRecords)
        {
            return cnameRecords.All(cr => zoneRecords.Where(r => r.GetRName() == cr.GetRName()).Length() == 1);
        }

        /// <summary>
        /// Checks whether there is more than a DNAME record for a domain name.
        /// </summary>
        /// <param name="dnameRecords">The dname records to check.</param>
        /// <param name="zoneRecords">The zone records.</param>
        /// <returns>True or false.</returns>
        public static Zen<bool> UniqueDname(Zen<IList<ResourceRecord>> dnameRecords, Zen<IList<ResourceRecord>> zoneRecords)
        {
            return dnameRecords.All(dr => zoneRecords.Where(r => And(
                r.GetRName() == dr.GetRName(),
                r.GetRType() == RecordType.DNAME)).Length() == 1);
        }

        /// <summary>
        /// Checks whether there is a domain name with both DNAME and NS records except when there is an SOA record.
        /// </summary>
        /// <param name="dnameRecords">The dname records to check.</param>
        /// <param name="zoneRecords">The zone records.</param>
        /// <param name="zoneDomain">The zone domain.</param>
        /// <returns>True or false.</returns>
        public static Zen<bool> DnameNs(Zen<IList<ResourceRecord>> dnameRecords, Zen<IList<ResourceRecord>> zoneRecords, Zen<DomainName> zoneDomain)
        {
            return dnameRecords.All(dr => Not(zoneRecords.Any(r => And(
                r.GetRName() == dr.GetRName(),
                r.GetRName() != zoneDomain,
                r.GetRType() == RecordType.NS))));
        }

        /// <summary>
        /// Checks whether there is a record with domain name for which a DNAME record domain name is a proper prefix.
        /// </summary>
        /// <param name="dnameRecords">The dname records to check.</param>
        /// <param name="zoneRecords">The zone records.</param>
        /// <returns>True or false.</returns>
        public static Zen<bool> DnamePrefix(Zen<IList<ResourceRecord>> dnameRecords, Zen<IList<ResourceRecord>> zoneRecords)
        {
            return dnameRecords.All(dr => Not(zoneRecords.Any(r => And(
                r.GetRName() != dr.GetRName(),
                Utils.IsPrefix(dr.GetRName(), r.GetRName())))));
        }

        /// <summary>
        /// Checks if there are NS records which are proper prefixes of another NS records (except when there is an SOA).
        /// </summary>
        /// <param name="nsRecords">The NS records.</param>
        /// <param name="zoneRecords">The zone records.</param>
        /// <param name="zoneDomain">The zone domain.</param>
        /// <returns>True or false.</returns>
        public static Zen<bool> NsPrefix(Zen<IList<ResourceRecord>> nsRecords, Zen<IList<ResourceRecord>> zoneRecords, Zen<DomainName> zoneDomain)
        {
            return nsRecords.All(ns => Not(zoneRecords.Any(r => And(
                         r.GetRName() != ns.GetRName(),
                         zoneDomain != ns.GetRName(),
                         r.GetRType() == RecordType.NS,
                         Utils.IsPrefix(ns.GetRName(), r.GetRName())))));
        }

        /// <summary>
        /// Checks whether every record has another record which is a prefix of it except when they have a zone domain name.
        /// </summary>
        /// <param name="records">The records.</param>
        /// <param name="zoneRecords">The zone records.</param>
        /// <param name="zoneDomain">The zone domain.</param>
        /// <returns>True or false.</returns>
        public static Zen<bool> PrefixClosed(Zen<IList<ResourceRecord>> records, Zen<IList<ResourceRecord>> zoneRecords, Zen<DomainName> zoneDomain)
        {
            return records.All(r => Or(
                zoneDomain == r.GetRName(),
                zoneRecords.Any(zr => And(
                    zr.GetRName() != r.GetRName(),
                    Utils.IsPrefix(zr.GetRName(), r.GetRName()),
                    zr.GetRName().GetValue().Length() == r.GetRName().GetValue().Length() - 1))));
        }

        /// <summary>
        /// Checks if the set of resource records 𝑅 are prefix-closed for the domain name of the zone.
        /// Checks by checking for every record of type N, are there any other records with the same name, and
        /// if any other valid records exist for which this record is a prefix.
        /// </summary>
        /// <param name="nRecords">The records with type N.</param>
        /// <param name="zoneRecords">The zone records.</param>
        /// <returns>True or false.</returns>
        public static Zen<bool> NRecordCheck(Zen<IList<ResourceRecord>> nRecords, Zen<IList<ResourceRecord>> zoneRecords)
        {
            return nRecords.All(nr => And(
                zoneRecords.Where(r => r.GetRName() == nr.GetRName()).Length() == 1,
                zoneRecords.Any(r => And(
                    Utils.IsPrefix(nr.GetRName(), r.GetRName()),
                    r.GetRType() != RecordType.N))));
        }

        /// <summary>
        /// Checks if the NS answer is an alias record or there is a DNAME record for the prefix of it.
        /// </summary>
        /// <param name="nsRecords">The NS records.</param>
        /// <param name="zoneRecords">The zone records.</param>
        /// <returns>True or false.</returns>
        public static Zen<bool> NsDnameCname(Zen<IList<ResourceRecord>> nsRecords, Zen<IList<ResourceRecord>> zoneRecords)
        {
            return nsRecords.All(ns => Not(
                zoneRecords.Any(r => Or(
                    And(
                        r.GetRType() == RecordType.CNAME,
                        r.GetRName() == ns.GetRData()),
                    And(
                        r.GetRType() == RecordType.DNAME,
                        Utils.IsPrefix(r.GetRName(), ns.GetRData()),
                        r.GetRName() != ns.GetRData())))));
        }

        /// <summary>
        /// Checks if the required glue records exist in the zone.
        /// </summary>
        /// <param name="nsRecords">The NS records.</param>
        /// <param name="zoneRecords">The zone records.</param>
        /// <param name="zoneDomain">The zone domain.</param>
        /// <returns>True or false.</returns>
        public static Zen<bool> GlueRecords(Zen<IList<ResourceRecord>> nsRecords, Zen<IList<ResourceRecord>> zoneRecords, Zen<DomainName> zoneDomain)
        {
            return nsRecords.All(ns => If(
                Utils.IsPrefix(zoneDomain, ns.GetRData()),
                zoneRecords.Any(r => And(r.GetRName() == ns.GetRData(), Or(r.GetRType() == RecordType.A, r.GetRType() == RecordType.AAAA))),
                true));
        }
    }

    /// <summary>
    /// Zone Zen extension methods.
    /// </summary>
    public static class ZoneExtensions
    {
        /// <summary>
        /// Gets the records in a zone.
        /// </summary>
        /// <param name="z">The zone.</param>
        /// <returns>The list of resource records of the zone.</returns>
        public static Zen<IList<ResourceRecord>> GetRecords(this Zen<Zone> z) => z.GetField<Zone, IList<ResourceRecord>>("Records");

        /// <summary>
        /// Returns a list of  conditions for a well-formed zone.
        /// </summary>
        /// <param name="z">The zone.</param>
        /// <returns>A boolean.</returns>
        public static IList<Zen<bool>> ValidZoneConditions(this Zen<Zone> z)
        {
            IList<Zen<bool>> predicates = new List<Zen<bool>>();

            // All the records should be valid.
            predicates.Add(z.GetRecords().All(ResourceRecordExtensions.IsValidRecord));

            // All the records should be unique. (RFC 2181)
            predicates.Add(ZoneUtils.RecordUniqueness(z.GetRecords(), z.GetRecords()));

            // Zone should be non-empty.
            predicates.Add(Not(z.GetRecords().IsEmpty()));

            // Zone should have exactly one SOA record. (Condition 1; RFC 1035)
            predicates.Add(z.GetRecords().Where(r => r.GetRType() == RecordType.SOA).Length() == 1);

            var zoneDomain = z.GetRecords().Where(r => r.GetRType() == RecordType.SOA).At(0).Value().GetRName();

            // The zone domain should be prefix to all the resource records domain name. (Condition 3; RFC1034)
            predicates.Add(Implies(
                z.GetRecords().Where(r => r.GetRType() == RecordType.SOA).At(0).HasValue(),
                z.GetRecords().All(r => Utils.IsPrefix(zoneDomain, r.GetRName()))));

            // There can be only one CNAME record for a domain name and also there can be no other type if there is a CNAME record. (Conditions 5 & 6; RFC 1034)
            predicates.Add(ZoneUtils.SingleCname(z.GetRecords().Where(r => r.GetRType() == RecordType.CNAME), z.GetRecords()));

            Zen<IList<ResourceRecord>> dnameRecords = z.GetRecords().Where(r => r.GetRType() == RecordType.DNAME);

            // There can be only one DNAME record for a domain name. (Condition 7; RFC 6672)
            predicates.Add(ZoneUtils.UniqueDname(dnameRecords, z.GetRecords()));

            // A domain name cannot have both DNAME and NS records unless there is an SOA record. (Condition 8; RFC 6672)
            predicates.Add(ZoneUtils.DnameNs(dnameRecords, z.GetRecords(), zoneDomain));

            // If there is a DNAME record for a domain name 𝑑, then there cannot be any records for domain names for which 𝑑 is a proper prefix. (Condition 9; RFC 6672)
            predicates.Add(ZoneUtils.DnamePrefix(dnameRecords, z.GetRecords()));

            // If there is an NS record for a domain name 𝑑 but not an SOA record, then there cannot be any NS records for domain names for which 𝑑 is a proper prefix. (Condition 10; RFC 1034)
            predicates.Add(ZoneUtils.NsPrefix(z.GetRecords().Where(r => r.GetRType() == RecordType.NS), z.GetRecords(), zoneDomain));

            // Prefix-closed. (Condition 12)
            predicates.Add(ZoneUtils.PrefixClosed(z.GetRecords(), z.GetRecords(), zoneDomain));
            predicates.Add(ZoneUtils.NRecordCheck(z.GetRecords().Where(r => r.GetRType() == RecordType.N), z.GetRecords()));

            // NS answer should not be related to a CNAME or a DNAME record. (RFC 2181)
            predicates.Add(ZoneUtils.NsDnameCname(z.GetRecords().Where(r => r.GetRType() == RecordType.NS), z.GetRecords()));

            // Glue records have to exist for both in-domain and sibling domain. (In-bailiwick rule of RFC 8499)
            predicates.Add(ZoneUtils.GlueRecords(z.GetRecords().Where(r => r.GetRType() == RecordType.NS), z.GetRecords(), zoneDomain));

            return predicates;
        }

        /// <summary>
        /// Whether a zone is well-formed.
        /// </summary>
        /// <param name="z">The zone.</param>
        /// <returns>A boolean.</returns>
        public static Zen<bool> IsValidZone(this Zen<Zone> z)
        {
            return z.ValidZoneConditions().Aggregate(AndIf);
        }
    }
}
