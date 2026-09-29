#include "BrawlerEditorLibrary.h"

#include "StreetsOfBerlin.h"
#include "PaperSprite.h"
#include "Engine/Texture2D.h"
#include "Materials/MaterialInterface.h"
#include "UObject/Package.h"

#if WITH_EDITOR
#include "AssetRegistry/AssetRegistryModule.h"
#endif

UPaperSprite* UBrawlerEditorLibrary::CreateSpriteFromTexture(UTexture2D* Texture, const FString& PackagePath, const FString& AssetName, UMaterialInterface* Material)
{
#if WITH_EDITOR
	if (!Texture)
	{
		UE_LOG(LogStreetsOfBerlin, Warning, TEXT("CreateSpriteFromTexture: keine Textur fuer %s"), *AssetName);
		return nullptr;
	}

	const FString LongName = PackagePath / AssetName;
	UPaperSprite* Sprite = LoadObject<UPaperSprite>(nullptr, *(LongName + TEXT(".") + AssetName), nullptr, LOAD_NoWarn | LOAD_Quiet);
	bool bCreated = false;
	if (!Sprite)
	{
		UPackage* Package = CreatePackage(*LongName);
		Package->FullyLoad();
		Sprite = NewObject<UPaperSprite>(Package, *AssetName, RF_Public | RF_Standalone | RF_Transactional);
		bCreated = true;
	}

	FSpriteAssetInitParameters Params;
	Params.SetTextureAndFill(Texture);
	if (Material)
	{
		Params.DefaultMaterialOverride = Material;
		Params.AlternateMaterialOverride = Material;
	}
	Sprite->Modify();
	Sprite->InitializeSprite(Params);
	Sprite->PostEditChange();
	Sprite->MarkPackageDirty();

	if (bCreated)
	{
		FAssetRegistryModule::AssetCreated(Sprite);
	}
	return Sprite;
#else
	return nullptr;
#endif
}
