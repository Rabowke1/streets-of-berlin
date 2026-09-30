#pragma once

#include "CoreMinimal.h"
#include "UObject/Object.h"
#include "InputCoreTypes.h"
#include "BrawlerMenu.generated.h"

class ABrawlerGameMode;
class UBrawlerSettings;

UENUM()
enum class EMenuScreen : uint8
{
	Main,
	Select,
	Options,
	Controls,
	Pause
};

enum class EMenuInput : uint8
{
	Up,
	Down,
	Left,
	Right,
	Ok,
	Back,
	Start
};

struct FMenuLevel
{
	EMenuScreen Screen = EMenuScreen::Main;
	int32 Sel = 0;
	/** Spalte im Steuerungsmenue (0/1 Tastatur, 2 Gamepad) */
	int32 Col = 0;
};

/**
 * Menue-Logik (Titel, Figurenauswahl, Optionen, Steuerung, Pause). Gezeichnet wird im ABrawlerHUD,
 * die Eingaben kommen vom ABrawlerPlayerController (laeuft auch waehrend der Pause).
 */
UCLASS()
class STREETSOFBERLIN_API UBrawlerMenu : public UObject
{
	GENERATED_BODY()

public:
	void Init(ABrawlerGameMode* InGameMode, UBrawlerSettings* InSettings);

	bool IsActive() const { return Stack.Num() > 0; }
	const FMenuLevel* Top() const { return Stack.Num() ? &Stack.Last() : nullptr; }
	void Reset() { Stack.Reset(); WaitAction = INDEX_NONE; }
	void Reset(EMenuScreen Screen);
	void Open(EMenuScreen Screen);
	void Close();
	void Input(EMenuInput In);

	/** Neubelegen: wartet auf Taste (Spalte 0/1) bzw. Gamepad-Knopf (Spalte 2) */
	bool IsWaiting() const { return WaitAction != INDEX_NONE; }
	int32 GetWaitAction() const { return WaitAction; }
	int32 GetWaitSlot() const { return WaitSlot; }
	/** true = Taste wurde verbraucht */
	bool CaptureKey(const FKey& Key);

	int32 GetItemCount(EMenuScreen Screen) const;
	FString GetItemLabel(EMenuScreen Screen, int32 Index) const;
	/** Wert rechts neben dem Eintrag (z.B. "AN", "70 %"), leer = keiner */
	FString GetItemValue(EMenuScreen Screen, int32 Index) const;
	bool IsItemDimmed(EMenuScreen Screen, int32 Index) const;
	/** Index der Aktion in einer Zeile des Steuerungsmenues, sonst INDEX_NONE */
	int32 GetControlsAction(int32 Index) const;

	UBrawlerSettings* GetSettings() const { return Settings; }

private:
	void Activate(int32 Index);
	void Adjust(int32 Index, int32 Dir);
	void Beep(float Volume = 0.35f) const;

	TArray<FMenuLevel> Stack;
	int32 WaitAction = INDEX_NONE;
	int32 WaitSlot = 0;

	TWeakObjectPtr<ABrawlerGameMode> GameMode;

	UPROPERTY()
	TObjectPtr<UBrawlerSettings> Settings;
};
