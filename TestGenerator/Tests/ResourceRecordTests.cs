namespace Tests
{
    using System.Collections.Generic;
    using System.Diagnostics.CodeAnalysis;
    using Authoritative;
    using Microsoft.VisualStudio.TestTools.UnitTesting;
    using ZenLib;
    using static ZenLib.Language;

    /// <summary>
    /// Tests for Zen working with classes.
    /// </summary>
    [TestClass]
    [ExcludeFromCodeCoverage]
    public class ResourceRecordTests
    {
        /// <summary>
        /// Test equality of two domain names.
        /// </summary>
        [TestMethod]
        public void TestDomainNameEquality()
        {
            var function = new ZenFunction<DomainName, DomainName, bool>((d1, d2) => d1 == d2);

            var d1 = new DomainName { Value = new List<byte> { 1, 2 } };
            var d2 = new DomainName { Value = new List<byte> { 1, 2 } };
            Assert.IsTrue(function.Evaluate(d1, d2));

            // Search for a case where the lists are equal but not the domain names. (C# '==' for lists compares references)
            var input = function.Find((d1, d2, t) => And(Not(t), d1.Equals(d2)));
            Assert.IsFalse(input.HasValue);
        }

        /// <summary>
        /// Test wildcard records.
        /// </summary>
        [TestMethod]
        public void TestWildcardRecord()
        {
            var function = new ZenFunction<ResourceRecord, bool>(ResourceRecordExtensions.IsWildcardRecord);

            var record = new ResourceRecord
            {
                RName = new DomainName { Value = new List<byte> { 0, 2, 1 } },
                RType = RecordType.A,
                RData = new DomainName { Value = new List<byte> { } },
            };
            Assert.IsTrue(function.Evaluate(record));

            var r = ResourceRecord.Create(
               new DomainName { Value = new List<byte> { 0, 2 } },
               RecordType.DNAME,
               new DomainName { Value = new List<byte> { } });
            Assert.AreEqual(r.IsWildcardRecord(), false);
        }

        /// <summary>
        /// Test the prefix nature of domain names.
        /// </summary>
        [TestMethod]
        public void TestDomainNamePrefix()
        {
            var function = new ZenFunction<DomainName, DomainName, bool>(Utils.IsPrefix);
            Assert.AreEqual(function.Evaluate(new DomainName { Value = new List<byte> { } }, new DomainName { Value = new List<byte> { } }), true);

            Assert.AreEqual(function.Evaluate(new DomainName { Value = new List<byte> { } }, new DomainName { Value = new List<byte> { 0 } }), true);
            Assert.AreEqual(function.Evaluate(new DomainName { Value = new List<byte> { 0 } }, new DomainName { Value = new List<byte> { } }), false);

            Assert.AreEqual(function.Evaluate(new DomainName { Value = new List<byte> { 0 } }, new DomainName { Value = new List<byte> { 0 } }), true);
            Assert.AreEqual(function.Evaluate(new DomainName { Value = new List<byte> { 0, 0 } }, new DomainName { Value = new List<byte> { 0 } }), false);

            Assert.AreEqual(function.Evaluate(new DomainName { Value = new List<byte> { 0 } }, new DomainName { Value = new List<byte> { 0, 0 } }), true);
            Assert.AreEqual(function.Evaluate(new DomainName { Value = new List<byte> { 2, 3 } }, new DomainName { Value = new List<byte> { 2, 3 } }), true);

            Assert.AreEqual(function.Evaluate(new DomainName { Value = new List<byte> { 3 } }, new DomainName { Value = new List<byte> { 2 } }), false);
            Assert.AreEqual(function.Evaluate(new DomainName { Value = new List<byte> { 2, 3 } }, new DomainName { Value = new List<byte> { 2, 4 } }), false);
        }

        /// <summary>
        /// Test resource record validity.
        /// </summary>
        [TestMethod]
        public void TestRRValidityEvaluate()
        {
            var function = new ZenFunction<ResourceRecord, bool>(ResourceRecordExtensions.IsValidRecord);

            var soa = new ResourceRecord
            {
                RName = new DomainName { Value = new List<byte> { 0, 2 } },
                RType = RecordType.SOA,
                RData = new DomainName { Value = new List<byte> { } },
            };
            Assert.IsTrue(function.Evaluate(soa));

            var r1 = new ResourceRecord
            {
                RName = new DomainName { Value = new List<byte> { 0, 2, 3 } },
                RType = RecordType.AAAA,
                RData = new DomainName { Value = new List<byte> { } },
            };
            Assert.IsTrue(function.Evaluate(r1));

            var r2 = new ResourceRecord
            {
                RName = new DomainName { Value = new List<byte> { 0, 2, 3, 4 } },
                RType = RecordType.CNAME,
                RData = new DomainName { Value = new List<byte> { 0 } },
            };
            Assert.IsTrue(function.Evaluate(r2));

            // Name should be non-empty.
            var r3 = new ResourceRecord
            {
                RName = new DomainName { Value = new List<byte> { } },
                RType = RecordType.SOA,
                RData = new DomainName { Value = new List<byte> { } },
            };
            Assert.IsFalse(function.Evaluate(r3));

            // Rdata should be empty for A.
            var r4 = new ResourceRecord
            {
                RName = new DomainName { Value = new List<byte> { 0, 2 } },
                RType = RecordType.A,
                RData = new DomainName { Value = new List<byte> { 0 } },
            };
            Assert.IsFalse(function.Evaluate(r3));

            // Rdata should be non-empty for DNAME.
            var r5 = ResourceRecord.Create(
                new DomainName { Value = new List<byte> { 0, 2 } },
                RecordType.DNAME,
                new DomainName { Value = new List<byte> { } });
            Assert.AreEqual(r5.IsValidRecord(), false);

            // Wildcard cannot have a DNAME record.
            var r6 = ResourceRecord.Create(
                new DomainName { Value = new List<byte> { 0, 2, 1 } },
                RecordType.DNAME,
                new DomainName { Value = new List<byte> { 0 } });
            Assert.AreEqual(r6.IsValidRecord(), false);
        }

        /// <summary>
        /// Test resource record validity.
        /// </summary>
        [TestMethod]
        public void TestRRValidityVerify()
        {
            var function = new ZenFunction<ResourceRecord, bool>(ResourceRecordExtensions.IsValidRecord);

            // Name should be non-empty
            var result = function.Find((r, v) => And(v, r.GetRName().GetValue().IsEmpty()));
            Assert.IsFalse(result.HasValue);

            // Rdata should be empty for N
            result = function.Find((r, v) => And(v, r.GetRType() == RecordType.N, Not(r.GetRData().GetValue().IsEmpty())));
            Assert.IsFalse(result.HasValue);

            // Rdata should be non-empty for NS
            result = function.Find((r, v) => And(v, r.GetRType() == RecordType.NS, r.GetRData().GetValue().IsEmpty()));
            Assert.IsFalse(result.HasValue);
        }
    }
}
