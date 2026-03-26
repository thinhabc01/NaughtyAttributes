using UnityEngine;

namespace NaughtyAttributes.Test
{
    public class HorizontalLineSerializedPropertyTest : MonoBehaviour
    {
        [field: SerializeField]
        [HorizontalLine(color: EColor.Red)]
        public int RedLineProperty { get; private set; }

        [field: SerializeField]
        [HorizontalLine(6.0f, EColor.Blue)]
        public Vector3 BlueLineProperty { get; private set; }
    }
}
