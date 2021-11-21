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
                z.IsValidZoneForRRLookup(),
                q.IsValidQuery(),
                Utils.IsPrefix(z.GetRecords().Where(r => r.GetRType() == RecordType.SOA).At(0).Value().GetRName(), q.GetQName()),
                rrs == ServerModel.GetRelevantRRs(q, z));
        }
        static void GenerateTestsExhaustiveRRLookup(string outputDir, int maxLength)
        {
            var watch = System.Diagnostics.Stopwatch.StartNew();
            var function = Function<IList<ResourceRecord>, Query, Zone, Response>(ServerModel.RRLookup);
            int i = 0;
            var intermediateTimer = System.Diagnostics.Stopwatch.StartNew();
            Console.WriteLine($"{DateTime.Now} Starting the constraint solving for maximum length {maxLength} for exhaustive test generation of RRLookup");
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
                    Console.WriteLine($"{DateTime.Now} Time for generation of tests from {i - 100} - {i}: {intermediateTimer.ElapsedMilliseconds} ms");
                    intermediateTimer = System.Diagnostics.Stopwatch.StartNew();
                }
            }
            watch.Stop();
            Console.WriteLine($"{DateTime.Now} Total time to generate {i} tests for RRLookup: {watch.ElapsedMilliseconds} ms");
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
            for (var j = 1; j < ZoneExtensions.ValidZoneConditions(Zone.Create(new List<ResourceRecord>())).Count(); j++)
            {
                var watch = System.Diagnostics.Stopwatch.StartNew();
                var function = Function<Zone, bool>(ZoneExtensions.IsValidZone);
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
                    FileInfo file = new FileInfo(outputDir + "/FalseCond_" + s + "/ZenZoneFiles/" + i + ".json");
                    file.Directory.Create();
                    File.WriteAllText(file.FullName, info);
                    i++;
                }
                watch.Stop();
                Console.WriteLine($"{DateTime.Now} Total execution time to generate {i} invalid zone files for false indicies {s}: {watch.ElapsedMilliseconds} ms");
            }
        }

        [Flags]
        public enum FunctionsEnum
        {
            None = 0x0,
            RRLookup = 0x1,
            InvalidZoneFiles = 0x2,
        }

        public class Options
        {
            [Option('o', "outputDir", Default = "Results/", HelpText = "The path to the folder to output the generated tests.")]
            public string OutputDir { get; set; }

            [Option('f', "function", Default = FunctionsEnum.RRLookup, HelpText = "Generate tests for either 'RRLookup' (1) or generate invalid zone files 'InvalidZoneFiles' (2).")]
            public FunctionsEnum Function { get; set; }

            [Option('l', "length", Default = 4, HelpText = "The maximum number of records in a zone and the maximum length of a domain.")]
            public int MaximumLength { get; set; }
        }
        static void Main(string[] args)
        {
            var parser = new Parser(with =>
            {
                // ignore case for enum values
                with.CaseInsensitiveEnumValues = true;
                with.HelpWriter = Parser.Default.Settings.HelpWriter;
            });
            parser.ParseArguments<Options>(args)
                   .WithParsed(o =>
                   {
                       if (o.Function == FunctionsEnum.RRLookup)
                       {
                           var outputPath = Path.GetFullPath(o.OutputDir) + "/ValidZoneFileTests/ZenTests/";
                           Directory.CreateDirectory(outputPath);
                           GenerateTestsExhaustiveRRLookup(outputPath, o.MaximumLength);
                       }
                       else
                       {
                           GenerateInvalidZones(Path.GetFullPath(o.OutputDir) + "/InvalidZoneFileTests/", o.MaximumLength);
                       }
                   });
        }
    }
}
