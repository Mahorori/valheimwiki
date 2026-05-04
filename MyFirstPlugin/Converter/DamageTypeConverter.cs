using Newtonsoft.Json;
using System;

namespace MyFirstPlugin.Converter
{
    internal class DamageTypeConverter : JsonConverter<HitData.DamageType>
    {
        public override void WriteJson(JsonWriter writer, HitData.DamageType value, JsonSerializer serializer)
        {
            writer.WriteValue(value.ToString());
        }

        public override HitData.DamageType ReadJson(JsonReader reader, Type objectType, HitData.DamageType existingValue, bool hasExistingValue, JsonSerializer serializer)
        {
            var obj = Newtonsoft.Json.Linq.JObject.Load(reader);

            if (reader.Value == null)
                return default(HitData.DamageType);

            var str = reader.Value.ToString();

            if (Enum.TryParse<HitData.DamageType>(str, out var result))
                return result;

            throw new JsonSerializationException($"Invalid value '{str}' for enum {objectType.Name}");
        }
    }
}
