namespace Tests
{
    using System.Collections.Generic;
    using System.Diagnostics.CodeAnalysis;
    using System.Linq;
    using Authoritative;
    using Microsoft.VisualStudio.TestTools.UnitTesting;
    using ZenLib;
    using static ZenLib.Language;

    /// <summary>
    /// Tests for Zen working with classes.
    /// </summary>
    [TestClass]
    [ExcludeFromCodeCoverage]
    public class ServerLookupTests
    {
        /// <summary>
        /// Test maximum of a list.
        /// </summary>
        [TestMethod]
        public void TestMaxofList()
        {
            var function = Function<IList<ushort>, ushort>(ServerModel.MaxofList);
            Assert.AreEqual(function.Evaluate(new List<ushort> { 3, 2, 1 }), (ushort)3);
            Assert.AreEqual(function.Evaluate(new List<ushort> { }), (ushort)0);
            Assert.AreEqual(function.Evaluate(new List<ushort> { 1 }), (ushort)1);
            Assert.AreEqual(function.Evaluate(new List<ushort> { 2, 2 }), (ushort)2);
            Assert.AreEqual(function.Evaluate(new List<ushort> { 1, 2 }), (ushort)2);
            Assert.AreEqual(function.Evaluate(new List<ushort> { 2, 1 }), (ushort)2);
            Assert.AreEqual(function.Evaluate(new List<ushort> { 2, 0, 0 }), (ushort)2);
            Assert.AreEqual(function.Evaluate(new List<ushort> { 1, 2, 3 }), (ushort)3);
        }

        /// <summary>
        /// Test MaximalPrefixMatch returns correctly the common number of prefix labels.
        /// </summary>
        [TestMethod]
        public void TestMaximalPrefixMatch()
        {
            var function = Function<DomainName, DomainName, ushort>(Utils.MaximalPrefixMatch);
            Assert.AreEqual(function.Evaluate(new DomainName { Value = new List<byte> { } }, new DomainName { Value = new List<byte> { } }), (ushort)0);
            Assert.AreEqual(function.Evaluate(new DomainName { Value = new List<byte> { } }, new DomainName { Value = new List<byte> { 0 } }), (ushort)0);
            Assert.AreEqual(function.Evaluate(new DomainName { Value = new List<byte> { 2, 0 } }, new DomainName { Value = new List<byte> { } }), (ushort)0);
            Assert.AreEqual(function.Evaluate(new DomainName { Value = new List<byte> { 0 } }, new DomainName { Value = new List<byte> { 0 } }), (ushort)1);
            Assert.AreEqual(function.Evaluate(new DomainName { Value = new List<byte> { 2 } }, new DomainName { Value = new List<byte> { 2, 3 } }), (ushort)1);
            Assert.AreEqual(function.Evaluate(new DomainName { Value = new List<byte> { 2, 3 } }, new DomainName { Value = new List<byte> { 2 } }), (ushort)1);
            Assert.AreEqual(function.Evaluate(new DomainName { Value = new List<byte> { 2, 3 } }, new DomainName { Value = new List<byte> { 2, 3 } }), (ushort)2);
            Assert.AreEqual(function.Evaluate(new DomainName { Value = new List<byte> { 2, 3 } }, new DomainName { Value = new List<byte> { 2, 4 } }), (ushort)1);

            // Maximal prefix match is symmetric
            var result = function.Find((x, y, l) => l != Utils.MaximalPrefixMatch(y, x));
            Assert.IsFalse(result.HasValue);
        }

        /// <summary>
        /// Test IsDomainWildcardMatch returns correctly.
        /// </summary>
        [TestMethod]
        public void TestDomainWildcardMatch()
        {
            var function = Function<DomainName, DomainName, bool>(Utils.IsDomainWildcardMatch);
            Assert.IsFalse(function.Evaluate(new DomainName { Value = new List<byte> { } }, new DomainName { Value = new List<byte> { } }));
            Assert.IsFalse(function.Evaluate(new DomainName { Value = new List<byte> { } }, new DomainName { Value = new List<byte> { 1 } }));
            Assert.IsTrue(function.Evaluate(new DomainName { Value = new List<byte> { 2, 0 } }, new DomainName { Value = new List<byte> { 2, 1 } }));
            Assert.IsTrue(function.Evaluate(new DomainName { Value = new List<byte> { 2, 0, 1 } }, new DomainName { Value = new List<byte> { 2, 1 } }));
            Assert.IsTrue(function.Evaluate(new DomainName { Value = new List<byte> { 2, 1, 2, 3 } }, new DomainName { Value = new List<byte> { 2, 1, 1 } }));
            Assert.IsFalse(function.Evaluate(new DomainName { Value = new List<byte> { 2, 1 } }, new DomainName { Value = new List<byte> { 2, 1 } }));
        }

        /// <summary>
        /// Test GetRelevantRRs returns the correct set of RRs for a valid zone and query.
        /// </summary>
        [TestMethod]
        public void TestGetRelevantRRs()
        {
            var function = Function<Query, Zone, IList<ResourceRecord>>(ServerModel.GetRelevantRRs);
            var soa = new ResourceRecord
            {
                RName = new DomainName { Value = new List<byte> { 32 } },
                RType = RecordType.SOA,
                RData = new DomainName { Value = new List<byte> { } },
            };
            var z1 = new Zone { Records = new List<ResourceRecord> { soa } };
            var result = function.Evaluate(new Query { QName = new DomainName { Value = new List<byte> { 1 } }, QType = RecordType.SOA }, z1);
            Assert.IsFalse(result.Any());

            result = function.Evaluate(new Query { QName = new DomainName { Value = new List<byte> { 32 } }, QType = RecordType.SOA }, z1);
            Assert.IsTrue(result.Count() == 1);
            Assert.IsTrue(soa.Equals(result.First()));

            result = function.Evaluate(new Query { QName = new DomainName { Value = new List<byte> { 32 } }, QType = RecordType.AAAA }, z1);
            Assert.IsTrue(result.Count() == 1);
            Assert.IsTrue(soa.Equals(result.First()));

            result = function.Evaluate(new Query { QName = new DomainName { Value = new List<byte> { 32, 3 } }, QType = RecordType.SOA }, z1);
            Assert.IsTrue(result.Count() == 1);
            Assert.IsTrue(soa.Equals(result.First()));

            result = function.Evaluate(new Query { QName = new DomainName { Value = new List<byte> { 32, 5 } }, QType = RecordType.A }, z1);
            Assert.IsTrue(result.Count() == 1);
            Assert.IsTrue(soa.Equals(result.First()));

            var ns = new ResourceRecord
            {
                RName = new DomainName { Value = new List<byte> { 32, 5 } },
                RType = RecordType.NS,
                RData = new DomainName { Value = new List<byte> { 32, 5, 6 } },
            };
            var glue = new ResourceRecord
            {
                RName = new DomainName { Value = new List<byte> { 32, 5, 6 } },
                RType = RecordType.A,
                RData = new DomainName { Value = new List<byte> { } },
            };
            var z2 = new Zone { Records = new List<ResourceRecord> { soa, ns, glue } };

            result = function.Evaluate(new Query { QName = new DomainName { Value = new List<byte> { 32, 5, 6 } }, QType = RecordType.A }, z2);
            Assert.IsTrue(result.Count() == 1);
            Assert.IsTrue(ns.Equals(result.Last()));

            result = function.Evaluate(new Query { QName = new DomainName { Value = new List<byte> { 32, 5 } }, QType = RecordType.NS }, z2);
            Assert.IsTrue(result.Count() == 1);
            Assert.IsTrue(ns.Equals(result.Last()));

            var cname = new ResourceRecord
            {
                RName = new DomainName { Value = new List<byte> { 32, 23 } },
                RType = RecordType.CNAME,
                RData = new DomainName { Value = new List<byte> { 0, 2 } },
            };
            var z3 = new Zone { Records = new List<ResourceRecord> { soa, cname } };

            result = function.Evaluate(new Query { QName = new DomainName { Value = new List<byte> { 32, 3 } }, QType = RecordType.A }, z3);
            Assert.IsTrue(result.Count() == 1);
            Assert.IsTrue(soa.Equals(result.First()));

            result = function.Evaluate(new Query { QName = new DomainName { Value = new List<byte> { 32, 23 } }, QType = RecordType.A }, z3);
            Assert.IsTrue(result.Count() == 1);
            Assert.IsTrue(cname.Equals(result.First()));

            var emptyRRs = function.Find((q, z, rrs) => And(
                z.IsValidZoneForRRLookup(),
                q.IsValidQuery(),
                Utils.IsPrefix(z.GetRecords().Where(r => r.GetRType() == RecordType.SOA).At(0).Value().GetRName(), q.GetQName()),
                rrs.IsEmpty()), listSize: 3);
            Assert.IsFalse(emptyRRs.HasValue);

            // All the relevant records should have the same domain name.
            var differentNames = function.Find((q, z, rrs) => And(
                z.IsValidZoneForRRLookup(),
                q.IsValidQuery(),
                Utils.IsPrefix(z.GetRecords().Where(r => r.GetRType() == RecordType.SOA).At(0).Value().GetRName(), q.GetQName()),
                rrs.Length() >= 2,
                rrs.At(0).Value().GetRName() != rrs.At(1).Value().GetRName()), listSize: 3);
            Assert.IsFalse(differentNames.HasValue);
        }

        /// <summary>
        /// Test GetRelevantRRs returns the correct set of RRs for a valid zone and query involving wildcard records.
        /// </summary>
        [TestMethod]
        public void TestGetRelevantRRsWildcardTest()
        {
            var function = Function<Query, Zone, IList<ResourceRecord>>(ServerModel.GetRelevantRRs);
            var soa = new ResourceRecord
            {
                RName = new DomainName { Value = new List<byte> { 32 } },
                RType = RecordType.SOA,
                RData = new DomainName { Value = new List<byte> { } },
            };
            var concrete = new ResourceRecord
            {
                RName = new DomainName { Value = new List<byte> { 32, 2 } },
                RType = RecordType.NS,
                RData = new DomainName { Value = new List<byte> { 0, 2 } },
            };
            var wildcard = new ResourceRecord
            {
                RName = new DomainName { Value = new List<byte> { 32, 1 } },
                RType = RecordType.CNAME,
                RData = new DomainName { Value = new List<byte> { 0, 2 } },
            };
            var z1 = new Zone { Records = new List<ResourceRecord> { soa, concrete, wildcard } };
            var result = function.Evaluate(new Query { QName = new DomainName { Value = new List<byte> { 32, 2 } }, QType = RecordType.A }, z1);
            Assert.IsTrue(result.Count() == 1);
            Assert.IsTrue(concrete.Equals(result.First()));

            result = function.Evaluate(new Query { QName = new DomainName { Value = new List<byte> { 32, 4 } }, QType = RecordType.A }, z1);
            Assert.IsTrue(result.Count() == 1);
            Assert.IsTrue(wildcard.Equals(result.First()));

            result = function.Evaluate(new Query { QName = new DomainName { Value = new List<byte> { 32, 4, 5 } }, QType = RecordType.A }, z1);
            Assert.IsTrue(result.Count() == 1);
            Assert.IsTrue(wildcard.Equals(result.First()));

            result = function.Evaluate(new Query { QName = new DomainName { Value = new List<byte> { 32, 1, 4 } }, QType = RecordType.A }, z1);
            Assert.IsTrue(result.Count() == 1);
            Assert.IsTrue(wildcard.Equals(result.First()));

            var wild1 = new ResourceRecord
            {
                RName = new DomainName { Value = new List<byte> { 32, 1 } },
                RType = RecordType.A,
                RData = new DomainName { Value = new List<byte> { } },
            };
            var wild2 = new ResourceRecord
            {
                RName = new DomainName { Value = new List<byte> { 32, 1, 1 } },
                RType = RecordType.CNAME,
                RData = new DomainName { Value = new List<byte> { 0, 2 } },
            };
            var z = new Zone { Records = new List<ResourceRecord> { soa, wild1, wild2 } };
            var q = new Query { QName = new DomainName { Value = new List<byte> { 32, 1, 5 } }, QType = RecordType.A };
            result = function.Evaluate(q, z);
            Assert.IsTrue(result.Count() == 1);

            var r3 = new ResourceRecord
            {
                RName = new DomainName { Value = new List<byte> { 32, 6, 4 } },
                RType = RecordType.A,
                RData = new DomainName { Value = new List<byte> { } },
            };

            var r4 = new ResourceRecord
            {
                RName = new DomainName { Value = new List<byte> { 32, 6 } },
                RType = RecordType.N,
                RData = new DomainName { Value = new List<byte> { } },
            };
            z = new Zone { Records = new List<ResourceRecord> { soa, r3, r4 } };
            q = new Query { QName = new DomainName { Value = new List<byte> { 32, 6 } }, QType = RecordType.A };
            result = function.Evaluate(q, z);
            Assert.IsTrue(result.Count() == 1);
            Assert.IsTrue(result[0].Equals(r4));
        }

        private Zen<bool> RRLookupConstraints(Zen<Zone> z, Zen<Query> q, Zen<IList<ResourceRecord>> rrs)
        {
            return And(
                z.IsValidZoneForRRLookup(),
                q.IsValidQuery(),
                Utils.IsPrefix(z.GetRecords().Where(r => r.GetRType() == RecordType.SOA).At(0).Value().GetRName(), q.GetQName()),
                rrs == ServerModel.GetRelevantRRs(q, z));
        }

        /// <summary>
        /// Check whether ExactMatch returns the correct answer for a valid zone, query and relevant records.
        /// </summary>
        [TestMethod]
        public void TestExactMatch()
        {
            var function = Function<IList<ResourceRecord>, Query, Zone, Response>(ServerModel.ExactMatch);

            // ExactMatch should not return NX response on valid inputs
            var nxResponse = function.Find((rrs, q, z, res) => And(
               RRLookupConstraints(z, q, rrs),
               rrs.At(0).Value().GetRName() == q.GetQName(),
               res.GetResTag() == Tag.R2), listSize: 3);
            Assert.IsFalse(nxResponse.HasValue);

            // When the query type is CNAME there should be case where it is returned with ANS (E1) instead of ANSQ (E2).
            var cnameTypeMatch = function.Find((rrs, q, z, res) => And(
               RRLookupConstraints(z, q, rrs),
               rrs.At(0).Value().GetRName() == q.GetQName(),
               q.GetQType() == rrs.At(0).Value().GetRType(),
               q.GetQType() == RecordType.CNAME,
               res.GetResTag() == Tag.E1), listSize: 3);

            Assert.IsTrue(cnameTypeMatch.HasValue);
            var result = function.Evaluate(cnameTypeMatch.Value.Item1, cnameTypeMatch.Value.Item2, cnameTypeMatch.Value.Item3);
            Assert.IsTrue(cnameTypeMatch.Value.Item1.Count() == 1);
            Assert.IsTrue(result.ResRecords.Count() == 1);
            Assert.IsTrue(cnameTypeMatch.Value.Item1[0].Equals(result.ResRecords[0]));

            // Valid inputs should always lead to a valid response.
            var invalidResponse = function.Find((rrs, q, z, res) => And(
               RRLookupConstraints(z, q, rrs),
               rrs.At(0).Value().GetRName() == q.GetQName(),
               Not(res.IsValidResponse())), listSize: 3);
            Assert.IsFalse(invalidResponse.HasValue);

            // When the query type is CNAME the response is never a ANSQ (E2) for valid inputs.
            var cnameTypeAnsQ = function.Find((rrs, q, z, res) => And(
               RRLookupConstraints(z, q, rrs),
               rrs.At(0).Value().GetRName() == q.GetQName(),
               q.GetQType() == RecordType.CNAME,
               res.GetResTag() == Tag.E2), listSize: 3);
            Assert.IsFalse(cnameTypeAnsQ.HasValue);

            // Find a ANSQ (E2) response for valid inputs.
            var ansqInputs = function.Find((rrs, q, z, res) => And(
               RRLookupConstraints(z, q, rrs),
               rrs.At(0).Value().GetRName() == q.GetQName(),
               res.GetResTag() == Tag.E2), listSize: 3);
            Assert.IsTrue(ansqInputs.HasValue);
            result = function.Evaluate(ansqInputs.Value.Item1, ansqInputs.Value.Item2, ansqInputs.Value.Item3);
            Assert.IsTrue(ansqInputs.Value.Item1.Count() == 1);
            Assert.IsTrue(result.ResRecords.Count() == 1);
            Assert.IsTrue(ansqInputs.Value.Item1[0].Equals(result.ResRecords[0]));
            Assert.IsTrue(result.RewrittenQuery.HasValue);
            Assert.IsTrue(result.RewrittenQuery.Value.QName.Equals(result.ResRecords[0].RData));
        }

        /// <summary>
        /// Check whether ExactMatch returns the correct answer for a valid zone, query and relevant records.
        /// </summary>
        [TestMethod]
        public void TestWildcardMatch()
        {
            var function = Function<IList<ResourceRecord>, Query, Zone, Response>(ServerModel.WildcardMatch);

            // WildcardMatch should not return NX response on valid inputs
            var nxResponse = function.Find((rrs, q, z, res) => And(
               RRLookupConstraints(z, q, rrs),
               Utils.IsDomainWildcardMatch(q.GetQName(), rrs.At(0).Value().GetRName()),
               res.GetResTag() == Tag.R2), listSize: 3);
            Assert.IsFalse(nxResponse.HasValue);

            // Find a ANSQ (W2) response for valid inputs.
            var ansqInputs = function.Find((rrs, q, z, res) => And(
               RRLookupConstraints(z, q, rrs),
               Utils.IsDomainWildcardMatch(q.GetQName(), rrs.At(0).Value().GetRName()),
               res.GetResTag() == Tag.W2), listSize: 3);
            Assert.IsTrue(ansqInputs.HasValue);
            var result = function.Evaluate(ansqInputs.Value.Item1, ansqInputs.Value.Item2, ansqInputs.Value.Item3);
            Assert.IsTrue(ansqInputs.Value.Item1.Count() == 1);
            Assert.IsTrue(result.ResRecords.Count() == 1);
            Assert.IsTrue(result.RewrittenQuery.HasValue);
            Assert.IsTrue(result.RewrittenQuery.Value.QName.Equals(result.ResRecords[0].RData));
        }

        /// <summary>
        /// Check ServerLookup output for an example.
        /// </summary>
        [TestMethod]
        public void TestServerLookupExample()
        {
            var function = Function<Query, Zone, Option<Response>>(ServerModel.ServerLookup);
            var soa = new ResourceRecord
            {
                RName = new DomainName { Value = new List<byte> { 8 } },
                RType = RecordType.SOA,
                RData = new DomainName { Value = new List<byte> { } },
            };
            var r1 = new ResourceRecord
            {
                RName = new DomainName { Value = new List<byte> { 8, 4 } },
                RType = RecordType.DNAME,
                RData = new DomainName { Value = new List<byte> { 0, 0 } },
            };
            var r2 = new ResourceRecord
            {
                RName = new DomainName { Value = new List<byte> { 8, 4 } },
                RType = RecordType.AAAA,
                RData = new DomainName { Value = new List<byte> { } },
            };
            var z = new Zone { Records = new List<ResourceRecord> { soa, r1, r2 } };
            var result = function.Evaluate(new Query { QName = new DomainName { Value = new List<byte> { 8, 4, 72 } }, QType = RecordType.AAAA }, z);
            Assert.IsTrue(result.HasValue);
            var v = result.Value;
            Assert.IsTrue(v.ResRecords.Count() == 2);
            Assert.IsTrue(r1.Equals(v.ResRecords.First()));
            Assert.IsTrue(v.ResRecords[1].RType == RecordType.CNAME);
            Assert.IsTrue(v.ResRecords[1].RData.Value.SequenceEqual(new List<byte> { 0, 0, 72 }));
            Assert.IsTrue(v.RewrittenQuery.HasValue);
            Assert.IsTrue(v.RewrittenQuery.Value.QName.Equals(v.ResRecords[1].RData));
        }
    }
}
