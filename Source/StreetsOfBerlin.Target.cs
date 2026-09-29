using UnrealBuildTool;

public class StreetsOfBerlinTarget : TargetRules
{
	public StreetsOfBerlinTarget(TargetInfo Target) : base(Target)
	{
		Type = TargetType.Game;
		DefaultBuildSettings = BuildSettingsVersion.Latest;
		IncludeOrderVersion = EngineIncludeOrderVersion.Latest;
		ExtraModuleNames.Add("StreetsOfBerlin");
	}
}
