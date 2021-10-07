namespace Samples
{
    using System;
    using System.Collections.Generic;
    using System.IO;
    using System.Linq;
    using System.Text.Json;
    using Authoritative;
    using CommandLine;
    using ZenLib;
    using static ZenLib.Language;

    class Program
    {
        private static string CreateJson(Query q, Zone z, IList<ResourceRecord> rrs, Response res)
        {
            var d = new Dictionary<string, Object>() { };
            d.Add("Relevant", rrs);
            d.Add("Query", q);
            d.Add("Zone", z);
            d.Add("Response", res);
            var options = new JsonSerializerOptions { WriteIndented = true };
            return JsonSerializer.Serialize(d, options);
        }

        private static Zen<bool> RRLookupConstraints(Zen<Zone> z, Zen<Query> q, Zen<IList<ResourceRecord>> rrs)
        {
            return And(
                z.IsValidZone(),
                q.IsValidQuery(),
                Utils.IsPrefix(z.GetRecords().Where(r => r.GetRType() == RecordType.SOA).At(0).Value().GetRName(), q.GetQName()),
                rrs == ServerModel.GetRelevantRRs(q, z));
        }
        static void GenerateTestsExhaustiveRRLookup(string outputDir, int maxLength)
        {
            var watch = System.Diagnostics.Stopwatch.StartNew();
            var function = new ZenFunction<IList<ResourceRecord>, Query, Zone, Response>(ServerModel.RRLookup);
            int i = 0;
            var intermediateTimer = System.Diagnostics.Stopwatch.StartNew();
            Console.WriteLine($"Starting the constraint solving for maximum length {maxLength}");
            foreach (var events in function.GenerateInputs(precondition: (rrs, q, z) => RRLookupConstraints(z, q, rrs), listSize: maxLength, checkSmallerLists: true))
            {
                var response = function.Evaluate(events.Item1, events.Item2, events.Item3);
                var info = CreateJson(events.Item2, events.Item3, events.Item1, response);
                FileInfo file = new FileInfo(outputDir + i + ".json");
                file.Directory.Create();
                File.WriteAllText(file.FullName, info);
                i++;
                if (i % 100 == 0)
                {
                    intermediateTimer.Stop();
                    Console.WriteLine($"Time for generation of tests from {i - 100} - {i}: {intermediateTimer.ElapsedMilliseconds} ms");
                    intermediateTimer = System.Diagnostics.Stopwatch.StartNew();
                }
            }
            watch.Stop();
            Console.WriteLine($"Total time to generate {i} tests: {watch.ElapsedMilliseconds} ms");
        }
        static void GenerateTestsZones()
        {
            var watch = System.Diagnostics.Stopwatch.StartNew();
            var function = new ZenFunction<Zone, bool>(ZoneExtensions.IsValidZone);
            int i = 0;
            var watchForSome = System.Diagnostics.Stopwatch.StartNew();
            foreach (var events in function.GenerateInputs(precondition: z => z.GetRecords().All(ResourceRecordExtensions.IsValidRecord), listSize: 4, checkSmallerLists: true))
            {
                var validity = function.Evaluate(events);
                var d = new Dictionary<string, object>() { };
                d.Add("Zone", events);
                d.Add("Valid", validity);
                var options = new JsonSerializerOptions { WriteIndented = true };
                var info = JsonSerializer.Serialize(d, options);
                FileInfo file = new FileInfo("Valid_Invalid/" + i + ".json");
                file.Directory.Create();
                File.WriteAllText(file.FullName, info);
                i++;
                if (i % 100 == 0)
                {
                    watchForSome.Stop();
                    Console.WriteLine($"Time for generation of {i - 100} - {i}: {watchForSome.ElapsedMilliseconds} ms");
                    watchForSome = System.Diagnostics.Stopwatch.StartNew();
                }
            }
            watch.Stop();
            Console.WriteLine($"Total time to generate {i} zone files: {watch.ElapsedMilliseconds} ms");
        }

        static Zen<bool> InvalidZonesGenerationHelper(IList<Zen<bool>> conditions, ISet<int> falseIndicies)
        {
            IList<Zen<bool>> predicates = new List<Zen<bool>>();
            for (var i = 0; i < conditions.Count; i++)
            {
                if (falseIndicies.Contains(i))
                {
                    predicates.Add(Not(conditions[i]));
                }
                else
                {
                    predicates.Add(conditions[i]);
                }
            }
            return predicates.Aggregate(AndIf);
        }

        static void GenerateInvalidZones(string outputDir, int maxLength)
        {
            for (var j = 0; j < ZoneExtensions.ValidZoneConditions(Zone.Create(new List<ResourceRecord>())).Count(); j++)
            {
                var watch = System.Diagnostics.Stopwatch.StartNew();
                var function = new ZenFunction<Zone, bool>(ZoneExtensions.IsValidZone);
                var falseIndicies = new HashSet<int> { j };
                var zones = function.FindAll((z, t) => InvalidZonesGenerationHelper(z.ValidZoneConditions(), falseIndicies), listSize: maxLength, checkSmallerLists: true).Take(100);
                function.Compile();
                int i = 0;
                var s = string.Join("_", falseIndicies);
                foreach (var input in zones)
                {
                    var d = new Dictionary<string, object>() { };
                    d.Add("Zone", input);
                    d.Add("Valid", function.Evaluate(input));
                    var options = new JsonSerializerOptions { WriteIndented = true };
                    var info = JsonSerializer.Serialize(d, options);
                    FileInfo file = new FileInfo(outputDir + "/FalseCond_" + s + "/ZoneFiles/" + i + ".json");
                    file.Directory.Create();
                    File.WriteAllText(file.FullName, info);
                    i++;
                }
                watch.Stop();
                Console.WriteLine($"Total execution time to generate {i} zone files for false indicies {s}: {watch.ElapsedMilliseconds} ms");
            }
        }

        [Flags]
        public enum FunctionsEnum
        {
            None = 0x0,
            QueryLookup = 0x1,
            InvalidZones = 0x2,
        }

        public class Options
        {
            [Option('o', "outputDir", Default = "Results/", HelpText = "The path to the folder to output the generated tests.")]
            public string OutputDir { get; set; }

            [Option('f', "function", Default = FunctionsEnum.QueryLookup, HelpText = "Generate tests for either 'QueryLookup' (1) or 'InvalidZones' (2).")]
            public FunctionsEnum Function { get; set; }

            [Option('l', "length", Default = 4, HelpText = "The maximum number of records in a zone and the maximum length of a domain.")]
            public int MaximumLength { get; set; }
        }
        static void Main(string[] args)
        {
            Settings.PreserveBranches = true;
            var parser = new Parser(with =>
            {
                // ignore case for enum values
                with.CaseInsensitiveEnumValues = true;
                with.HelpWriter = Parser.Default.Settings.HelpWriter;
            });
            parser.ParseArguments<Options>(args)
                   .WithParsed(o =>
                   {
                       if (o.Function == FunctionsEnum.QueryLookup)
                       {
                           Directory.CreateDirectory(Path.GetFullPath(o.OutputDir) + "/LookupTests/");
                           GenerateTestsExhaustiveRRLookup(Path.GetFullPath(o.OutputDir) + "/LookupTests/", o.MaximumLength);
                       }
                       else
                       {
                           GenerateInvalidZones(Path.GetFullPath(o.OutputDir) + "/InvalidZones/", o.MaximumLength);
                       }
                   });
        }
    }
}
