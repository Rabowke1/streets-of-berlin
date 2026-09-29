using UnrealBuildTool;

public class StreetsOfBerlinEditorTarget : TargetRules
{
	public StreetsOfBerlinEditorTarget(TargetInfo Target) : base(Target)
	{
		Type = TargetType.Editor;
		DefaultBuildSettings = BuildSettingsVersion.Latest;
		IncludeOrderVersion = EngineIncludeOrderVersion.Latest;
		ExtraModuleNames.Add("StreetsOfBerlin");
	}
}
