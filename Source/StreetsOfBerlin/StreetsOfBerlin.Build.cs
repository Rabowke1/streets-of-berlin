using UnrealBuildTool;

public class StreetsOfBerlin : ModuleRules
{
	public StreetsOfBerlin(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

		PublicDependencyModuleNames.AddRange(new string[]
		{
			"Core", "CoreUObject", "Engine", "InputCore", "Paper2D"
		});

		if (Target.bBuildEditor)
		{
			// Nur fuer den Asset-Import (BrawlerEditorLibrary)
			PrivateDependencyModuleNames.AddRange(new string[] { "UnrealEd", "AssetRegistry" });
		}
	}
}
