#include "BrawlerAssets.h"

#include "StreetsOfBerlin.h"
#include "PaperSprite.h"
#include "Sound/SoundBase.h"
#include "Engine/Texture2D.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "Materials/MaterialInterface.h"
#include "Misc/PackageName.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"

UBrawlerAssets* UBrawlerAssets::Get(const UObject* WorldContext)
{
	const UWorld* World = WorldContext ? WorldContext->GetWorld() : nullptr;
	UGameInstance* GI = World ? World->GetGameInstance() : nullptr;
	return GI ? GI->GetSubsystem<UBrawlerAssets>() : nullptr;
}

UObject* UBrawlerAssets::LoadCached(const FString& PackagePath, UClass* Class)
{
	if (TObjectPtr<UObject>* Found = ObjectCache.Find(PackagePath))
	{
		return *Found;
	}
	if (Missing.Contains(PackagePath))
	{
		return nullptr;
	}

	UObject* Obj = nullptr;
	if (FPackageName::DoesPackageExist(PackagePath))
	{
		const FString ObjectPath = PackagePath + TEXT(".") + FPackageName::GetShortName(PackagePath);
		Obj = StaticLoadObject(Class, nullptr, *ObjectPath, nullptr, LOAD_NoWarn | LOAD_Quiet);
	}

	if (Obj)
	{
		ObjectCache.Add(PackagePath, Obj);
	}
	else
	{
		Missing.Add(PackagePath);
	}
	return Obj;
}

const TArray<TObjectPtr<UPaperSprite>>& UBrawlerAssets::GetFrames(const FString& Folder, const FString& Prefix)
{
	const FString Key = Folder / Prefix;
	if (FBrawlerAnimFrames* Found = AnimCache.Find(Key))
	{
		return Found->Frames;
	}

	FBrawlerAnimFrames& Entry = AnimCache.Add(Key);
	for (int32 Index = 0; Index < 64; ++Index)
	{
		const FString Path = FString::Printf(TEXT("/Game/Sprites/%s/%s_%02d"), *Folder, *Prefix, Index);
		UPaperSprite* Sprite = Cast<UPaperSprite>(LoadCached(Path, UPaperSprite::StaticClass()));
		if (!Sprite)
		{
			break;
		}
		Entry.Frames.Add(Sprite);
	}

	if (Entry.Frames.Num() == 0)
	{
		UE_LOG(LogStreetsOfBerlin, Warning, TEXT("Keine Frames fuer %s gefunden. Wurden die Assets importiert (Content/Python/sob_import_assets.py)?"), *Key);
	}
	return Entry.Frames;
}

const TArray<TObjectPtr<UPaperSprite>>& UBrawlerAssets::GetCharAnim(const FString& SpriteSet, FName Anim)
{
	return GetFrames(SpriteSet, SpriteSet + TEXT("_") + Anim.ToString());
}

UPaperSprite* UBrawlerAssets::GetSprite(const FString& Folder, const FString& Name)
{
	return Cast<UPaperSprite>(LoadCached(FString::Printf(TEXT("/Game/Sprites/%s/%s"), *Folder, *Name), UPaperSprite::StaticClass()));
}

UTexture2D* UBrawlerAssets::GetTexture(const FString& Folder, const FString& Name)
{
	return Cast<UTexture2D>(LoadCached(FString::Printf(TEXT("/Game/Sprites/%s/Textures/T_%s"), *Folder, *Name), UTexture2D::StaticClass()));
}

USoundBase* UBrawlerAssets::GetSound(const FString& Name)
{
	return Cast<USoundBase>(LoadCached(FString::Printf(TEXT("/Game/Audio/%s"), *Name), USoundBase::StaticClass()));
}

UMaterialInterface* UBrawlerAssets::GetSpriteMaterial()
{
	if (!SpriteMaterial)
	{
		SpriteMaterial = LoadObject<UMaterialInterface>(nullptr, TEXT("/Paper2D/TranslucentUnlitSpriteMaterial.TranslucentUnlitSpriteMaterial"));
	}
	return SpriteMaterial;
}

void UBrawlerAssets::LoadAnchors()
{
	bAnchorsLoaded = true;
	const FString Path = FPaths::ProjectContentDir() / TEXT("Data/anchors.json");
	FString Text;
	if (!FFileHelper::LoadFileToString(Text, *Path))
	{
		UE_LOG(LogStreetsOfBerlin, Warning, TEXT("anchors.json nicht gefunden (%s) - Waffen werden nicht in der Hand gezeichnet."), *Path);
		return;
	}

	TSharedPtr<FJsonObject> Root;
	const TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(Text);
	if (!FJsonSerializer::Deserialize(Reader, Root) || !Root.IsValid())
	{
		UE_LOG(LogStreetsOfBerlin, Warning, TEXT("anchors.json konnte nicht gelesen werden."));
		return;
	}

	const TSharedPtr<FJsonObject>* Frames = nullptr;
	if (Root->TryGetObjectField(TEXT("frames"), Frames))
	{
		for (const auto& Pair : (*Frames)->Values)
		{
			const TArray<TSharedPtr<FJsonValue>>* Arr = nullptr;
			if (Pair.Value->TryGetArray(Arr) && Arr->Num() >= 3)
			{
				HandAnchors.Add(Pair.Key, FVector((*Arr)[0]->AsNumber(), (*Arr)[1]->AsNumber(), (*Arr)[2]->AsNumber()));
			}
		}
	}

	const TSharedPtr<FJsonObject>* Weapons = nullptr;
	if (Root->TryGetObjectField(TEXT("weapons"), Weapons))
	{
		for (const auto& Pair : (*Weapons)->Values)
		{
			const TSharedPtr<FJsonObject>* W = nullptr;
			if (!Pair.Value->TryGetObject(W))
			{
				continue;
			}
			const TArray<TSharedPtr<FJsonValue>>* Size = nullptr;
			const TArray<TSharedPtr<FJsonValue>>* Grip = nullptr;
			if ((*W)->TryGetArrayField(TEXT("size"), Size) && (*W)->TryGetArrayField(TEXT("grip"), Grip) && Size->Num() >= 2 && Grip->Num() >= 2)
			{
				WeaponGrips.Add(FName(*Pair.Key), FVector4((*Size)[0]->AsNumber(), (*Size)[1]->AsNumber(), (*Grip)[0]->AsNumber(), (*Grip)[1]->AsNumber()));
			}
		}
	}
}

bool UBrawlerAssets::GetHandAnchor(const FString& FrameName, FVector& OutAnchor)
{
	if (!bAnchorsLoaded)
	{
		LoadAnchors();
	}
	if (const FVector* Found = HandAnchors.Find(FrameName))
	{
		OutAnchor = *Found;
		return true;
	}
	return false;
}

bool UBrawlerAssets::GetWeaponGrip(FName Weapon, FVector2D& OutSize, FVector2D& OutGrip)
{
	if (!bAnchorsLoaded)
	{
		LoadAnchors();
	}
	if (const FVector4* Found = WeaponGrips.Find(Weapon))
	{
		OutSize = FVector2D(Found->X, Found->Y);
		OutGrip = FVector2D(Found->Z, Found->W);
		return true;
	}
	return false;
}
