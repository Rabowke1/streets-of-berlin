#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "BrawlerEditorLibrary.generated.h"

class UPaperSprite;
class UTexture2D;
class UMaterialInterface;

/**
 * Hilfsfunktionen fuer das Import-Skript (Content/Python/sob_import_assets.py).
 * Aus Python aufrufbar als unreal.BrawlerEditorLibrary.create_sprite_from_texture(...)
 */
UCLASS()
class STREETSOFBERLIN_API UBrawlerEditorLibrary : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()

public:
	/** Nur im Editor: erzeugt (oder aktualisiert) ein Paper2D-Sprite, das die ganze Textur abdeckt. */
	UFUNCTION(BlueprintCallable, Category = "Streets of Berlin|Editor")
	static UPaperSprite* CreateSpriteFromTexture(UTexture2D* Texture, const FString& PackagePath, const FString& AssetName, UMaterialInterface* Material);
};
