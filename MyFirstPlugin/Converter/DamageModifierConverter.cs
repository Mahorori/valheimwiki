using Newtonsoft.Json;
using System;

namespace MyFirstPlugin.Converter
{
    internal class DamageModifierConverter : JsonConverter<HitData.DamageModifier>
    {
        public override void WriteJson(JsonWriter writer, HitData.DamageModifier value, JsonSerializer serializer)
        {
            writer.WriteValue(value.ToString());
        }

        public override HitData.DamageModifier ReadJson(JsonReader reader, Type objectType, HitData.DamageModifier existingValue, bool hasExistingValue, JsonSerializer serializer)
        {
            var obj = Newtonsoft.Json.Linq.JObject.Load(reader);

            if (reader.Value == null)
                return default(HitData.DamageModifier);

            var str = reader.Value.ToString();

            if (Enum.TryParse<HitData.DamageModifier>(str, out var result))
                return result;

            throw new JsonSerializationException($"Invalid value '{str}' for enum {objectType.Name}");
        }
    }
}
