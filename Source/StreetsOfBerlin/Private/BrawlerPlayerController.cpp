#include "BrawlerPlayerController.h"

#include "BrawlerGameMode.h"
#include "BrawlerMenu.h"
#include "BrawlerPlayer.h"
#include "BrawlerSettings.h"
#include "Engine/World.h"

ABrawlerPlayerController::ABrawlerPlayerController()
{
	bShowMouseCursor = false;
	bAutoManageActiveCameraTarget = false;
	bShouldPerformFullTickWhenPaused = true;
	PrimaryActorTick.bTickEvenWhenPaused = true;
}

void ABrawlerPlayerController::BeginPlay()
{
	Super::BeginPlay();
	SetInputMode(FInputModeGameOnly());

	TArray<FKey> All;
	EKeys::GetAllKeys(All);
	for (const FKey& Key : All)
	{
		if (!Key.IsAxis1D() && !Key.IsAxis2D() && !Key.IsAxis3D() && !Key.IsMouseButton() && !Key.IsTouch())
		{
			BindableKeys.Add(Key);
		}
	}
}

bool ABrawlerPlayerController::AnyJustPressed(std::initializer_list<FKey> Keys) const
{
	for (const FKey& Key : Keys)
	{
		if (WasInputKeyJustPressed(Key))
		{
			return true;
		}
	}
	return false;
}

void ABrawlerPlayerController::TickRebind(ABrawlerGameMode* GM)
{
	UBrawlerMenu* Menu = GM->GetMenu();
	for (const FKey& Key : BindableKeys)
	{
		if (WasInputKeyJustPressed(Key) && Menu->CaptureKey(Key))
		{
			return;
		}
	}
}

void ABrawlerPlayerController::TickMenu(ABrawlerGameMode* GM)
{
	UBrawlerMenu* Menu = GM->GetMenu();
	const UBrawlerSettings* Settings = GM->GetSettings();

	// Stick als Richtungstasten (nur Flanken)
	const float SX = GetInputAnalogKeyState(EKeys::Gamepad_LeftX);
	const float SY = GetInputAnalogKeyState(EKeys::Gamepad_LeftY);
	const FIntPoint Dir(SX > 0.6f ? 1 : (SX < -0.6f ? -1 : 0), SY > 0.6f ? 1 : (SY < -0.6f ? -1 : 0));
	const bool bStickLeft = Dir.X < 0 && PrevStickDir.X >= 0;
	const bool bStickRight = Dir.X > 0 && PrevStickDir.X <= 0;
	const bool bStickUp = Dir.Y > 0 && PrevStickDir.Y <= 0;
	const bool bStickDown = Dir.Y < 0 && PrevStickDir.Y >= 0;
	PrevStickDir = Dir;

	const auto Bound = [this, Settings](EBrawlerAction A) { return Settings && Settings->WasPressed(this, A); };

	if (bStickUp || AnyJustPressed({ EKeys::Up, EKeys::Gamepad_DPad_Up }) || Bound(EBrawlerAction::Up))
	{
		Menu->Input(EMenuInput::Up);
	}
	if (bStickDown || AnyJustPressed({ EKeys::Down, EKeys::Gamepad_DPad_Down }) || Bound(EBrawlerAction::Down))
	{
		Menu->Input(EMenuInput::Down);
	}
	if (bStickLeft || AnyJustPressed({ EKeys::Left, EKeys::Gamepad_DPad_Left }) || Bound(EBrawlerAction::Left))
	{
		Menu->Input(EMenuInput::Left);
	}
	if (bStickRight || AnyJustPressed({ EKeys::Right, EKeys::Gamepad_DPad_Right }) || Bound(EBrawlerAction::Right))
	{
		Menu->Input(EMenuInput::Right);
	}
	if (AnyJustPressed({ EKeys::Enter, EKeys::SpaceBar, EKeys::Gamepad_FaceButton_Bottom }) || Bound(EBrawlerAction::Attack))
	{
		Menu->Input(EMenuInput::Ok);
	}
	else if (Bound(EBrawlerAction::Start))
	{
		Menu->Input(EMenuInput::Start);
	}
	else if (AnyJustPressed({ EKeys::Escape, EKeys::BackSpace, EKeys::Gamepad_FaceButton_Right }) || Bound(EBrawlerAction::Back))
	{
		Menu->Input(EMenuInput::Back);
	}
}

void ABrawlerPlayerController::PlayerTick(float DeltaTime)
{
	Super::PlayerTick(DeltaTime);

	ABrawlerGameMode* GM = GetWorld() ? Cast<ABrawlerGameMode>(GetWorld()->GetAuthGameMode()) : nullptr;
	if (!GM || !GM->GetMenu())
	{
		return;
	}
	UBrawlerMenu* Menu = GM->GetMenu();
	const UBrawlerSettings* Settings = GM->GetSettings();

	if (Menu->IsWaiting())
	{
		TickRebind(GM);
		return;
	}
	if (Menu->IsActive())
	{
		TickMenu(GM);
		return;
	}

	// Esc pausiert immer, auch wenn Start umbelegt wurde
	if ((Settings && Settings->WasPressed(this, EBrawlerAction::Start)) || WasInputKeyJustPressed(EKeys::Escape))
	{
		GM->OnStartPressed();
		if (Menu->IsActive())
		{
			return;
		}
	}

	ABrawlerPlayer* Player = GM->GetPlayer();
	if (!Player || IsPaused() || !Settings)
	{
		return;
	}

	FVector2D Move = FVector2D::ZeroVector;
	Move.X += Settings->IsDown(this, EBrawlerAction::Right) ? 1.f : 0.f;
	Move.X -= Settings->IsDown(this, EBrawlerAction::Left) ? 1.f : 0.f;
	Move.Y += Settings->IsDown(this, EBrawlerAction::Up) ? 1.f : 0.f;
	Move.Y -= Settings->IsDown(this, EBrawlerAction::Down) ? 1.f : 0.f;

	const FVector2D Stick(GetInputAnalogKeyState(EKeys::Gamepad_LeftX), GetInputAnalogKeyState(EKeys::Gamepad_LeftY));
	if (Stick.Size() > 0.25f)
	{
		Move += Stick;
	}
	Move.X = FMath::Clamp(Move.X, -1.0, 1.0);
	Move.Y = FMath::Clamp(Move.Y, -1.0, 1.0);
	Player->SetMoveInput(Move);

	if (Settings->WasPressed(this, EBrawlerAction::Attack))
	{
		Player->PressAttack();
	}
	if (Settings->WasPressed(this, EBrawlerAction::Jump))
	{
		Player->PressJump();
	}
	if (Settings->WasPressed(this, EBrawlerAction::Special))
	{
		Player->PressSpecial();
	}
	if (Settings->WasPressed(this, EBrawlerAction::Back))
	{
		Player->PressBackAttack();
	}
}
