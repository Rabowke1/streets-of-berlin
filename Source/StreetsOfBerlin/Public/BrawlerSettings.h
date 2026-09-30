#pragma once

#include "CoreMinimal.h"
#include "GameFramework/SaveGame.h"
#include "InputCoreTypes.h"
#include "BrawlerSettings.generated.h"

class APlayerController;

/** Belegbare Aktionen (Reihenfolge = Reihenfolge im Steuerungsmenue) */
UENUM()
enum class EBrawlerAction : uint8
{
	Left,
	Right,
	Up,
	Down,
	Attack,
	Jump,
	Special,
	Back,
	Start,
	Count UMETA(Hidden)
};

/** Zwei Tastatur-Tasten + ein Gamepad-Knopf pro Aktion */
USTRUCT()
struct FBrawlerKeyBinding
{
	GENERATED_BODY()

	UPROPERTY()
	FKey Key1;

	UPROPERTY()
	FKey Key2;

	UPROPERTY()
	FKey Pad;
};

/**
 * Spieleinstellungen: Musik/Sounds (an/aus + Lautstaerke), Tastenbelegung, zuletzt gewaehlte Figur.
 * Wird als SaveGame im Slot "SobSettings" gespeichert.
 */
UCLASS()
class STREETSOFBERLIN_API UBrawlerSettings : public USaveGame
{
	GENERATED_BODY()

public:
	static constexpr int32 NumActions = static_cast<int32>(EBrawlerAction::Count);
	/** Spalten im Steuerungsmenue: 0/1 = Tastatur, 2 = Gamepad */
	static constexpr int32 PadSlot = 2;

	static UBrawlerSettings* LoadOrCreate();
	void Save();
	void ResetControls();

	static const TCHAR* ActionLabel(EBrawlerAction Action);
	static FString KeyLabel(const FKey& Key);

	FKey GetKey(EBrawlerAction Action, int32 Slot) const;
	/** Belegt eine Taste neu; war sie schon vergeben, bekommt die andere Aktion die alte Taste (Tausch). */
	void BindKey(EBrawlerAction Action, int32 Slot, const FKey& Key);
	void ClearKey(EBrawlerAction Action, int32 Slot);

	bool IsDown(const APlayerController* PC, EBrawlerAction Action) const;
	bool WasPressed(const APlayerController* PC, EBrawlerAction Action) const;

	UPROPERTY()
	int32 Version = 1;

	UPROPERTY()
	bool bMusic = true;

	UPROPERTY()
	float MusicVolume = 0.7f;

	UPROPERTY()
	bool bSfx = true;

	UPROPERTY()
	float SfxVolume = 0.8f;

	UPROPERTY()
	FName Character = TEXT("Kai");

	UPROPERTY()
	TArray<FBrawlerKeyBinding> Bindings;

private:
	FKey& KeyRef(int32 ActionIndex, int32 Slot);
	void Sanitize();
};
