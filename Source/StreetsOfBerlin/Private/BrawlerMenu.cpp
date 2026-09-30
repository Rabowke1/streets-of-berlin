#include "BrawlerMenu.h"

#include "BrawlerGameMode.h"
#include "BrawlerPlayer.h"
#include "BrawlerSettings.h"
#include "Kismet/KismetSystemLibrary.h"

namespace
{
	constexpr int32 ControlsExtraRows = 2; // "Standard wiederherstellen", "Zurueck"
}

void UBrawlerMenu::Init(ABrawlerGameMode* InGameMode, UBrawlerSettings* InSettings)
{
	GameMode = InGameMode;
	Settings = InSettings;
}

void UBrawlerMenu::Reset(EMenuScreen Screen)
{
	Reset();
	FMenuLevel L;
	L.Screen = Screen;
	Stack.Add(L);
}

void UBrawlerMenu::Open(EMenuScreen Screen)
{
	FMenuLevel L;
	L.Screen = Screen;
	if (Screen == EMenuScreen::Select && Settings)
	{
		const TArray<FPlayerProfile>& Profiles = ABrawlerPlayer::GetProfiles();
		for (int32 I = 0; I < Profiles.Num(); ++I)
		{
			if (Profiles[I].Id == Settings->Character)
			{
				L.Sel = I;
			}
		}
	}
	Stack.Add(L);
	Beep();
}

void UBrawlerMenu::Close()
{
	WaitAction = INDEX_NONE;
	if (!Stack.Num())
	{
		return;
	}
	if (Stack.Last().Screen == EMenuScreen::Pause)
	{
		if (ABrawlerGameMode* GM = GameMode.Get())
		{
			GM->ResumeGame();
		}
		return;
	}
	if (Stack.Num() > 1)
	{
		Stack.Pop();
		Beep();
	}
}

void UBrawlerMenu::Beep(float Volume) const
{
	if (ABrawlerGameMode* GM = GameMode.Get())
	{
		GM->PlaySfx(TEXT("SFX_Pickup"), Volume, 0.02f);
	}
}

int32 UBrawlerMenu::GetItemCount(EMenuScreen Screen) const
{
	switch (Screen)
	{
	case EMenuScreen::Main: return 3;
	case EMenuScreen::Pause: return 3;
	case EMenuScreen::Options: return 6;
	case EMenuScreen::Controls: return UBrawlerSettings::NumActions + ControlsExtraRows;
	case EMenuScreen::Select: return ABrawlerPlayer::GetProfiles().Num();
	default: return 0;
	}
}

int32 UBrawlerMenu::GetControlsAction(int32 Index) const
{
	return Index >= 0 && Index < UBrawlerSettings::NumActions ? Index : INDEX_NONE;
}

FString UBrawlerMenu::GetItemLabel(EMenuScreen Screen, int32 Index) const
{
	switch (Screen)
	{
	case EMenuScreen::Main:
	{
		static const TCHAR* L[] = { TEXT("SPIEL STARTEN"), TEXT("OPTIONEN"), TEXT("BEENDEN") };
		return L[FMath::Clamp(Index, 0, 2)];
	}
	case EMenuScreen::Pause:
	{
		static const TCHAR* L[] = { TEXT("WEITER"), TEXT("OPTIONEN"), TEXT("ZUM TITEL") };
		return L[FMath::Clamp(Index, 0, 2)];
	}
	case EMenuScreen::Options:
	{
		static const TCHAR* L[] = { TEXT("MUSIK"), TEXT("MUSIK-LAUTSTÄRKE"), TEXT("SOUNDS"), TEXT("SOUND-LAUTSTÄRKE"), TEXT("STEUERUNG ANPASSEN"), TEXT("ZURÜCK") };
		return L[FMath::Clamp(Index, 0, 5)];
	}
	case EMenuScreen::Controls:
		if (GetControlsAction(Index) != INDEX_NONE)
		{
			return UBrawlerSettings::ActionLabel(static_cast<EBrawlerAction>(Index));
		}
		return Index == UBrawlerSettings::NumActions ? TEXT("STANDARD WIEDERHERSTELLEN") : TEXT("ZURÜCK");
	case EMenuScreen::Select:
		return ABrawlerPlayer::GetProfiles().IsValidIndex(Index) ? ABrawlerPlayer::GetProfiles()[Index].DisplayName : FString();
	default:
		return FString();
	}
}

FString UBrawlerMenu::GetItemValue(EMenuScreen Screen, int32 Index) const
{
	if (Screen != EMenuScreen::Options || !Settings)
	{
		return FString();
	}
	switch (Index)
	{
	case 0: return Settings->bMusic ? TEXT("AN") : TEXT("AUS");
	case 1: return FString::Printf(TEXT("%d %%"), FMath::RoundToInt(Settings->MusicVolume * 100.f));
	case 2: return Settings->bSfx ? TEXT("AN") : TEXT("AUS");
	case 3: return FString::Printf(TEXT("%d %%"), FMath::RoundToInt(Settings->SfxVolume * 100.f));
	default: return FString();
	}
}

bool UBrawlerMenu::IsItemDimmed(EMenuScreen Screen, int32 Index) const
{
	if (Screen != EMenuScreen::Options || !Settings)
	{
		return false;
	}
	return (Index == 1 && !Settings->bMusic) || (Index == 3 && !Settings->bSfx);
}

void UBrawlerMenu::Input(EMenuInput In)
{
	if (!Stack.Num() || IsWaiting())
	{
		return;
	}
	FMenuLevel& L = Stack.Last();
	const int32 Count = GetItemCount(L.Screen);
	if (Count <= 0)
	{
		return;
	}
	const bool bHorizontal = L.Screen == EMenuScreen::Select;
	const EMenuInput Prev = bHorizontal ? EMenuInput::Left : EMenuInput::Up;
	const EMenuInput Next = bHorizontal ? EMenuInput::Right : EMenuInput::Down;

	if (In == Prev || In == Next)
	{
		L.Sel = (L.Sel + (In == Next ? 1 : Count - 1)) % Count;
		Beep(0.2f);
		return;
	}
	if (!bHorizontal && (In == EMenuInput::Left || In == EMenuInput::Right))
	{
		const int32 Dir = In == EMenuInput::Left ? -1 : 1;
		if (L.Screen == EMenuScreen::Controls && GetControlsAction(L.Sel) != INDEX_NONE)
		{
			L.Col = FMath::Clamp(L.Col + Dir, 0, UBrawlerSettings::PadSlot);
			Beep(0.2f);
		}
		else
		{
			Adjust(L.Sel, Dir);
		}
		return;
	}
	const bool bPause = L.Screen == EMenuScreen::Pause;
	if (In == EMenuInput::Ok || (In == EMenuInput::Start && !bPause))
	{
		Activate(L.Sel);
	}
	else if (In == EMenuInput::Back || (In == EMenuInput::Start && bPause))
	{
		Close();
	}
}

void UBrawlerMenu::Adjust(int32 Index, int32 Dir)
{
	if (!Settings || !Stack.Num() || Stack.Last().Screen != EMenuScreen::Options)
	{
		return;
	}
	const auto Step = [Dir](float V) { return FMath::Clamp(FMath::RoundToFloat((V + Dir * 0.1f) * 10.f) / 10.f, 0.f, 1.f); };
	switch (Index)
	{
	case 0: Settings->bMusic = !Settings->bMusic; break;
	case 1: Settings->MusicVolume = Step(Settings->MusicVolume); break;
	case 2: Settings->bSfx = !Settings->bSfx; break;
	case 3: Settings->SfxVolume = Step(Settings->SfxVolume); break;
	default: return;
	}
	Settings->Save();
	if (ABrawlerGameMode* GM = GameMode.Get())
	{
		GM->ApplyAudioSettings();
	}
	Beep(0.3f);
}

void UBrawlerMenu::Activate(int32 Index)
{
	ABrawlerGameMode* GM = GameMode.Get();
	if (!GM || !Stack.Num())
	{
		return;
	}
	const FMenuLevel L = Stack.Last();
	switch (L.Screen)
	{
	case EMenuScreen::Main:
		if (Index == 0)
		{
			Open(EMenuScreen::Select);
		}
		else if (Index == 1)
		{
			Open(EMenuScreen::Options);
		}
		else
		{
			UKismetSystemLibrary::QuitGame(GM, nullptr, EQuitPreference::Quit, false);
		}
		break;
	case EMenuScreen::Pause:
		if (Index == 0)
		{
			GM->ResumeGame();
		}
		else if (Index == 1)
		{
			Open(EMenuScreen::Options);
		}
		else
		{
			GM->ReturnToTitle();
		}
		break;
	case EMenuScreen::Options:
		if (Index <= 3)
		{
			Adjust(Index, 1);
		}
		else if (Index == 4)
		{
			Open(EMenuScreen::Controls);
		}
		else
		{
			Close();
		}
		break;
	case EMenuScreen::Controls:
		if (GetControlsAction(Index) != INDEX_NONE)
		{
			WaitAction = Index;
			WaitSlot = L.Col;
			Beep();
		}
		else if (Index == UBrawlerSettings::NumActions)
		{
			Settings->ResetControls();
			Beep(0.6f);
		}
		else
		{
			Close();
		}
		break;
	case EMenuScreen::Select:
		if (ABrawlerPlayer::GetProfiles().IsValidIndex(Index))
		{
			GM->BeginGame(ABrawlerPlayer::GetProfiles()[Index].Id);
		}
		break;
	default:
		break;
	}
}

bool UBrawlerMenu::CaptureKey(const FKey& Key)
{
	if (!IsWaiting() || !Settings)
	{
		return false;
	}
	const bool bWantPad = WaitSlot == UBrawlerSettings::PadSlot;
	// Esc bzw. (beim Warten auf eine Taste) Gamepad-B brechen ab
	if (Key == EKeys::Escape || (!bWantPad && Key == EKeys::Gamepad_FaceButton_Right))
	{
		WaitAction = INDEX_NONE;
		return true;
	}
	if (Key.IsGamepadKey() != bWantPad)
	{
		return true; // falsches Geraet fuer diese Spalte: ignorieren
	}
	const EBrawlerAction Action = static_cast<EBrawlerAction>(WaitAction);
	if (Key == EKeys::BackSpace || Key == EKeys::Delete)
	{
		Settings->ClearKey(Action, WaitSlot);
	}
	else
	{
		Settings->BindKey(Action, WaitSlot, Key);
	}
	WaitAction = INDEX_NONE;
	Beep(0.6f);
	return true;
}
