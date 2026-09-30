#include "BrawlerSettings.h"

#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"

namespace
{
	const TCHAR* SlotName = TEXT("SobSettings");

	FBrawlerKeyBinding MakeBinding(const FKey& K1, const FKey& K2, const FKey& Pad)
	{
		FBrawlerKeyBinding B;
		B.Key1 = K1;
		B.Key2 = K2;
		B.Pad = Pad;
		return B;
	}

	TArray<FBrawlerKeyBinding> DefaultBindings()
	{
		return {
			MakeBinding(EKeys::A, EKeys::Left, EKeys::Gamepad_DPad_Left),
			MakeBinding(EKeys::D, EKeys::Right, EKeys::Gamepad_DPad_Right),
			MakeBinding(EKeys::W, EKeys::Up, EKeys::Gamepad_DPad_Up),
			MakeBinding(EKeys::S, EKeys::Down, EKeys::Gamepad_DPad_Down),
			MakeBinding(EKeys::J, FKey(), EKeys::Gamepad_FaceButton_Left),
			MakeBinding(EKeys::K, EKeys::SpaceBar, EKeys::Gamepad_FaceButton_Bottom),
			MakeBinding(EKeys::L, FKey(), EKeys::Gamepad_FaceButton_Top),
			MakeBinding(EKeys::I, FKey(), EKeys::Gamepad_FaceButton_Right),
			MakeBinding(EKeys::Enter, EKeys::P, EKeys::Gamepad_Special_Right),
		};
	}
}

UBrawlerSettings* UBrawlerSettings::LoadOrCreate()
{
	UBrawlerSettings* Settings = nullptr;
	if (UGameplayStatics::DoesSaveGameExist(SlotName, 0))
	{
		Settings = Cast<UBrawlerSettings>(UGameplayStatics::LoadGameFromSlot(SlotName, 0));
	}
	if (!Settings)
	{
		Settings = Cast<UBrawlerSettings>(UGameplayStatics::CreateSaveGameObject(UBrawlerSettings::StaticClass()));
	}
	Settings->Sanitize();
	return Settings;
}

void UBrawlerSettings::Sanitize()
{
	if (Bindings.Num() != NumActions)
	{
		Bindings = DefaultBindings();
	}
	MusicVolume = FMath::Clamp(MusicVolume, 0.f, 1.f);
	SfxVolume = FMath::Clamp(SfxVolume, 0.f, 1.f);
}

void UBrawlerSettings::Save()
{
	UGameplayStatics::SaveGameToSlot(this, SlotName, 0);
}

void UBrawlerSettings::ResetControls()
{
	Bindings = DefaultBindings();
	Save();
}

const TCHAR* UBrawlerSettings::ActionLabel(EBrawlerAction Action)
{
	switch (Action)
	{
	case EBrawlerAction::Left: return TEXT("LINKS");
	case EBrawlerAction::Right: return TEXT("RECHTS");
	case EBrawlerAction::Up: return TEXT("HOCH");
	case EBrawlerAction::Down: return TEXT("RUNTER");
	case EBrawlerAction::Attack: return TEXT("SCHLAG / AUFHEBEN");
	case EBrawlerAction::Jump: return TEXT("SPRUNG");
	case EBrawlerAction::Special: return TEXT("SPEZIAL");
	case EBrawlerAction::Back: return TEXT("RÜCKSCHLAG / WERFEN");
	case EBrawlerAction::Start: return TEXT("START / PAUSE");
	default: return TEXT("?");
	}
}

FString UBrawlerSettings::KeyLabel(const FKey& Key)
{
	return Key.IsValid() ? Key.GetDisplayName().ToString().ToUpper() : FString(TEXT("—"));
}

FKey& UBrawlerSettings::KeyRef(int32 ActionIndex, int32 Slot)
{
	FBrawlerKeyBinding& B = Bindings[ActionIndex];
	return Slot == 0 ? B.Key1 : (Slot == 1 ? B.Key2 : B.Pad);
}

FKey UBrawlerSettings::GetKey(EBrawlerAction Action, int32 Slot) const
{
	const int32 I = static_cast<int32>(Action);
	if (!Bindings.IsValidIndex(I))
	{
		return FKey();
	}
	const FBrawlerKeyBinding& B = Bindings[I];
	return Slot == 0 ? B.Key1 : (Slot == 1 ? B.Key2 : B.Pad);
}

void UBrawlerSettings::BindKey(EBrawlerAction Action, int32 Slot, const FKey& Key)
{
	const int32 Target = static_cast<int32>(Action);
	if (!Bindings.IsValidIndex(Target))
	{
		return;
	}
	const FKey Old = KeyRef(Target, Slot);
	// Tastatur-Spalten (0/1) und Gamepad-Spalte werden getrennt betrachtet
	const bool bPad = Slot == PadSlot;
	for (int32 A = 0; A < NumActions; ++A)
	{
		for (int32 S = bPad ? PadSlot : 0; S <= (bPad ? PadSlot : 1); ++S)
		{
			if ((A != Target || S != Slot) && KeyRef(A, S) == Key)
			{
				KeyRef(A, S) = A == Target ? FKey() : Old;
			}
		}
	}
	KeyRef(Target, Slot) = Key;
	Save();
}

void UBrawlerSettings::ClearKey(EBrawlerAction Action, int32 Slot)
{
	const int32 I = static_cast<int32>(Action);
	if (Bindings.IsValidIndex(I))
	{
		KeyRef(I, Slot) = FKey();
		Save();
	}
}

bool UBrawlerSettings::IsDown(const APlayerController* PC, EBrawlerAction Action) const
{
	for (int32 S = 0; S < 3; ++S)
	{
		const FKey K = GetKey(Action, S);
		if (K.IsValid() && PC->IsInputKeyDown(K))
		{
			return true;
		}
	}
	return false;
}

bool UBrawlerSettings::WasPressed(const APlayerController* PC, EBrawlerAction Action) const
{
	for (int32 S = 0; S < 3; ++S)
	{
		const FKey K = GetKey(Action, S);
		if (K.IsValid() && PC->WasInputKeyJustPressed(K))
		{
			return true;
		}
	}
	return false;
}
