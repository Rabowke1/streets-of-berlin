#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "BrawlerTypes.h"
#include "BrawlerAssets.generated.h"

class UPaperSprite;
class USoundBase;
class UTexture2D;
class UMaterialInterface;

/**
 * Laedt die (per Tools/ArtGen generierten und per Content/Python importierten)
 * Sprites, Texturen und Sounds anhand ihrer Namenskonvention und cached sie.
 *
 *   Sprite:  /Game/Sprites/<Folder>/<Name>
 *   Textur:  /Game/Sprites/<Folder>/Textures/T_<Name>
 *   Frames:  <Prefix>_00, <Prefix>_01, ...
 *   Sound:   /Game/Audio/<Name>
 */
UCLASS()
class STREETSOFBERLIN_API UBrawlerAssets : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:
	static UBrawlerAssets* Get(const UObject* WorldContext);

	/** Alle Frames einer Animation, z.B. GetFrames("Kai", "Kai_idle") */
	const TArray<TObjectPtr<UPaperSprite>>& GetFrames(const FString& Folder, const FString& Prefix);

	/** Charakter-Animation, z.B. GetCharAnim("Kai", "attack1") */
	const TArray<TObjectPtr<UPaperSprite>>& GetCharAnim(const FString& SpriteSet, FName Anim);

	UPaperSprite* GetSprite(const FString& Folder, const FString& Name);
	UTexture2D* GetTexture(const FString& Folder, const FString& Name);
	USoundBase* GetSound(const FString& Name);
	UMaterialInterface* GetSpriteMaterial();

	/** Hand-Anker eines Figuren-Frames: X/Y (Welt-Units ueber dem Fusspunkt), Z = Unterarm-Winkel in Grad */
	bool GetHandAnchor(const FString& FrameName, FVector& OutAnchor);
	/** Groesse und Griffpunkt (von links oben) eines Waffen-Sprites in Welt-Units */
	bool GetWeaponGrip(FName Weapon, FVector2D& OutSize, FVector2D& OutGrip);

private:
	UPROPERTY()
	TMap<FString, FBrawlerAnimFrames> AnimCache;

	UPROPERTY()
	TMap<FString, TObjectPtr<UObject>> ObjectCache;

	UPROPERTY()
	TObjectPtr<UMaterialInterface> SpriteMaterial;

	TSet<FString> Missing;

	void LoadAnchors();
	bool bAnchorsLoaded = false;
	TMap<FString, FVector> HandAnchors;
	TMap<FName, FVector4> WeaponGrips;

	UObject* LoadCached(const FString& ObjectPath, UClass* Class);
};
