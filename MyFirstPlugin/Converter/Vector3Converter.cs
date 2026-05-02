using Newtonsoft.Json;
using System;

namespace MyFirstPlugin.Converter
{
    public class Vector3Converter : JsonConverter<UnityEngine.Vector3>
    {
        public override void WriteJson(JsonWriter writer, UnityEngine.Vector3 value, JsonSerializer serializer)
        {
            writer.WriteStartObject();

            writer.WritePropertyName("x");
            writer.WriteValue(value.x);

            writer.WritePropertyName("y");
            writer.WriteValue(value.y);

            writer.WritePropertyName("z");
            writer.WriteValue(value.z);

            writer.WriteEndObject();
        }

        public override UnityEngine.Vector3 ReadJson(JsonReader reader, Type objectType, UnityEngine.Vector3 existingValue, bool hasExistingValue, JsonSerializer serializer)
        {
            var obj = Newtonsoft.Json.Linq.JObject.Load(reader);
            return new UnityEngine.Vector3(
                (float)obj["x"],
                (float)obj["y"],
                (float)obj["z"]
            );
        }
    }
}
