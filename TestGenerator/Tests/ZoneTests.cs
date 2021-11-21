namespace Tests
{
    using System.Collections.Generic;
    using System.Diagnostics.CodeAnalysis;
    using Authoritative;
    using Microsoft.VisualStudio.TestTools.UnitTesting;
    using static ZenLib.Language;

    /// <summary>
    /// Tests for Zen working with classes.
    /// </summary>
    [TestClass]
    [ExcludeFromCodeCoverage]
    public class ZoneTests
    {
        /// <summary>
        /// Test zone validity using examples.
        /// </summary>
        [TestMethod]
        public void TestZoneValidityEvaluate()
        {
            var function = Function<Zone, bool>(ZoneExtensions.IsValidZoneForRRLookup);

            var soa = new ResourceRecord
            {
                RName = new DomainName { Value = new List<byte> { 0, 2 } },
                RType = RecordType.SOA,
                RData = new DomainName { Value = new List<byte> { } },
            };

            var r1 = new ResourceRecord
            {
                RName = new DomainName { Value = new List<byte> { 0, 2, 3 } },
                RType = RecordType.AAAA,
                RData = new DomainName { Value = new List<byte> { } },
            };

            var r2 = new ResourceRecord
            {
                RName = new DomainName { Value = new List<byte> { 0, 2, 3, 4 } },
                RType = RecordType.CNAME,
                RData = new DomainName { Value = new List<byte> { 0 } },
            };

            var r4 = new ResourceRecord
            {
                RName = new DomainName { Value = new List<byte> { 0, 2, 3 } },
                RType = RecordType.N,
                RData = new DomainName { Value = new List<byte> { } },
            };
            var z = Zone.Create(new List<ResourceRecord> { soa, r1, r2 });
            Assert.AreEqual(z.IsValidZoneForRRLookup(), true);

            Zone zn = new Zone { Records = new List<ResourceRecord> { soa, r1, r2 } };
            Assert.IsTrue(function.Evaluate(zn));

            Zone invalid = new Zone { Records = new List<ResourceRecord> { r1, r2 } };
            Assert.IsFalse(function.Evaluate(invalid));

            Assert.IsFalse(function.Evaluate(new Zone { Records = new List<ResourceRecord> { soa, r2 } }));
            Assert.IsTrue(function.Evaluate(new Zone { Records = new List<ResourceRecord> { soa, r2, r4 } }));
        }

        /// <summary>
        /// Test zone validity using Find.
        /// </summary>
        [TestMethod]
        public void TestZoneValidityVerify()
        {
            var function = Function<Zone, bool>(ZoneExtensions.IsValidZoneForRRLookup);

            // Zone should have exactly one SOA record.
            var multipleSoa = function.Find((z, t) => And(z.GetRecords().Where(r => r.GetRType() == RecordType.SOA).Length() != 1, t), listSize: 3);
            Assert.IsFalse(multipleSoa.HasValue);

            // Find a zone which is valid and not prefix-closed.
            var notPrefix = function.Find((z, t) => And(
                Not(z.GetRecords().All(r => Utils.IsPrefix(z.GetRecords().Where(r => r.GetRType() == RecordType.SOA).At(0).Value().GetRName(), r.GetRName()))),
                t), listSize: 3);
            Assert.IsFalse(notPrefix.HasValue);

            // Find a valid zone which has two CNAME records for the same name.
            var multipleCname = function.Find((z, t) => And(
                z.GetRecords().Where(r => r.GetRType() == RecordType.CNAME).Length() > 2,
                z.GetRecords().Where(r => r.GetRType() == RecordType.CNAME).At(0).Value().GetRName() == z.GetRecords().Where(r => r.GetRType() == RecordType.CNAME).At(1).Value().GetRName(),
                t), listSize: 3);
            Assert.IsFalse(multipleCname.HasValue);
        }
    }
}
