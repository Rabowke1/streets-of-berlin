#include "BrawlerPlayerController.h"

#include "BrawlerGameMode.h"
#include "BrawlerPlayer.h"
#include "InputCoreTypes.h"
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

bool ABrawlerPlayerController::AnyDown(std::initializer_list<FKey> Keys) const
{
	for (const FKey& Key : Keys)
	{
		if (IsInputKeyDown(Key))
		{
			return true;
		}
	}
	return false;
}

void ABrawlerPlayerController::PlayerTick(float DeltaTime)
{
	Super::PlayerTick(DeltaTime);

	ABrawlerGameMode* GM = GetWorld() ? Cast<ABrawlerGameMode>(GetWorld()->GetAuthGameMode()) : nullptr;
	if (!GM)
	{
		return;
	}

	if (AnyJustPressed({ EKeys::Enter, EKeys::Gamepad_Special_Right, EKeys::P }))
	{
		if (GM->GetFlow() == EBrawlerFlow::Playing || GM->GetFlow() == EBrawlerFlow::Intro)
		{
			SetPause(!IsPaused());
		}
		else
		{
			GM->OnStartPressed();
		}
	}

	ABrawlerPlayer* Player = GM->GetPlayer();
	if (!Player || IsPaused())
	{
		return;
	}

	FVector2D Move = FVector2D::ZeroVector;
	Move.X += AnyDown({ EKeys::D, EKeys::Right, EKeys::Gamepad_DPad_Right }) ? 1.f : 0.f;
	Move.X -= AnyDown({ EKeys::A, EKeys::Left, EKeys::Gamepad_DPad_Left }) ? 1.f : 0.f;
	Move.Y += AnyDown({ EKeys::W, EKeys::Up, EKeys::Gamepad_DPad_Up }) ? 1.f : 0.f;
	Move.Y -= AnyDown({ EKeys::S, EKeys::Down, EKeys::Gamepad_DPad_Down }) ? 1.f : 0.f;

	const FVector2D Stick(GetInputAnalogKeyState(EKeys::Gamepad_LeftX), GetInputAnalogKeyState(EKeys::Gamepad_LeftY));
	if (Stick.Size() > 0.25f)
	{
		Move += Stick;
	}
	Move.X = FMath::Clamp(Move.X, -1.0, 1.0);
	Move.Y = FMath::Clamp(Move.Y, -1.0, 1.0);
	Player->SetMoveInput(Move);

	if (AnyJustPressed({ EKeys::J, EKeys::Gamepad_FaceButton_Left }))
	{
		Player->PressAttack();
	}
	if (AnyJustPressed({ EKeys::K, EKeys::SpaceBar, EKeys::Gamepad_FaceButton_Bottom }))
	{
		Player->PressJump();
	}
	if (AnyJustPressed({ EKeys::L, EKeys::Gamepad_FaceButton_Top }))
	{
		Player->PressSpecial();
	}
	if (AnyJustPressed({ EKeys::I, EKeys::Gamepad_FaceButton_Right }))
	{
		Player->PressBackAttack();
	}
}
