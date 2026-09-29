#include "BrawlerEntity.h"

#include "BrawlerAssets.h"
#include "PaperSprite.h"
#include "PaperSpriteComponent.h"
#include "Components/SceneComponent.h"

ABrawlerEntity::ABrawlerEntity()
{
	PrimaryActorTick.bCanEverTick = true;

	Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
	SetRootComponent(Root);

	Shadow = CreateDefaultSubobject<UPaperSpriteComponent>(TEXT("Shadow"));
	Shadow->SetupAttachment(Root);
	Shadow->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Shadow->SetGenerateOverlapEvents(false);
	Shadow->CastShadow = false;

	Sprite = CreateDefaultSubobject<UPaperSpriteComponent>(TEXT("Sprite"));
	Sprite->SetupAttachment(Root);
	Sprite->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Sprite->SetGenerateOverlapEvents(false);
	Sprite->CastShadow = false;
}

void ABrawlerEntity::BeginPlay()
{
	Super::BeginPlay();

	if (UBrawlerAssets* Assets = UBrawlerAssets::Get(this))
	{
		if (UMaterialInterface* Mat = Assets->GetSpriteMaterial())
		{
			Sprite->SetMaterial(0, Mat);
			Shadow->SetMaterial(0, Mat);
		}
		if (Shadow->GetSprite() == nullptr && ShadowScale > 0.f)
		{
			Shadow->SetSprite(Assets->GetSprite(TEXT("Effects"), TEXT("FX_Shadow")));
		}
	}
	Shadow->SetVisibility(ShadowScale > 0.f);
	UpdateRender();
}

void ABrawlerEntity::SetBeltPosition(float InX, float InDepth, float InHeight)
{
	PosX = InX;
	Depth = InDepth;
	Height = InHeight;
	UpdateRender();
}

void ABrawlerEntity::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	if (HitstopTimer > 0.f)
	{
		HitstopTimer -= DeltaSeconds;
		ShakeTimer = HitstopTimer;
		UpdateRender();
		return;
	}
	ShakeTimer = 0.f;

	TickEntity(DeltaSeconds);
	if (!IsValid(this))
	{
		return; // wurde in TickEntity zerstoert
	}
	UpdateAnimation(DeltaSeconds);
	UpdateRender();
}

void ABrawlerEntity::PlayFrames(const FString& Folder, const FString& Prefix, float FPS, bool bLoop, bool bRestart)
{
	const FString Key = Folder / Prefix;
	AnimFPS = FPS;
	bAnimLoop = bLoop;
	if (Key == AnimKey && !bRestart)
	{
		return;
	}

	AnimKey = Key;
	AnimTime = 0.f;
	AnimFrame = 0;
	bAnimFinished = false;
	CurrentFrames.Reset();
	if (UBrawlerAssets* Assets = UBrawlerAssets::Get(this))
	{
		CurrentFrames = Assets->GetFrames(Folder, Prefix);
	}
	if (CurrentFrames.Num() > 0)
	{
		Sprite->SetSprite(CurrentFrames[0]);
	}
}

void ABrawlerEntity::SetStaticSprite(UPaperSprite* InSprite)
{
	CurrentFrames.Reset();
	if (InSprite)
	{
		CurrentFrames.Add(InSprite);
	}
	AnimKey.Reset();
	AnimFrame = 0;
	bAnimFinished = true;
	Sprite->SetSprite(InSprite);
}

void ABrawlerEntity::SetAnimFrame(int32 Frame)
{
	if (CurrentFrames.Num() == 0)
	{
		return;
	}
	AnimFrame = FMath::Clamp(Frame, 0, CurrentFrames.Num() - 1);
	AnimTime = AnimFrame / FMath::Max(AnimFPS, 0.01f);
	Sprite->SetSprite(CurrentFrames[AnimFrame]);
}

void ABrawlerEntity::UpdateAnimation(float DeltaSeconds)
{
	const int32 Num = CurrentFrames.Num();
	if (Num == 0 || AnimFPS <= 0.f)
	{
		return;
	}

	AnimTime += DeltaSeconds;
	int32 Frame = FMath::FloorToInt(AnimTime * AnimFPS);
	if (bAnimLoop)
	{
		Frame %= Num;
	}
	else if (Frame >= Num)
	{
		Frame = Num - 1;
		bAnimFinished = true;
	}

	if (Frame != AnimFrame || Sprite->GetSprite() != CurrentFrames[Frame])
	{
		AnimFrame = Frame;
		Sprite->SetSprite(CurrentFrames[Frame]);
	}
}

void ABrawlerEntity::UpdateRender()
{
	SetActorLocation(Brawler::ToWorld(PosX, Depth, 0.f));

	float ShakeX = 0.f;
	if (ShakeTimer > 0.f)
	{
		ShakeX = (FMath::FRand() - 0.5f) * 8.f;
	}

	Sprite->SetRelativeLocation(FVector(ShakeX, 1.f, Height + SpriteFootOffset * SpriteScale));
	Sprite->SetRelativeScale3D(FVector(Facing * SpriteScale, 1.f, SpriteScale));

	const float ShadowFade = FMath::Clamp(1.f - Height / 400.f, 0.35f, 1.f);
	Shadow->SetRelativeLocation(FVector(0.f, 0.f, 0.f));
	Shadow->SetRelativeScale3D(FVector(ShadowScale * ShadowFade, 1.f, ShadowScale * ShadowFade));

	const int32 Priority = bUseDepthSort ? Brawler::SortForDepth(Depth, SortOffset) : FixedSortPriority;
	if (Sprite->TranslucencySortPriority != Priority)
	{
		Sprite->SetTranslucentSortPriority(Priority);
	}
	if (Shadow->TranslucencySortPriority != Brawler::SortShadow)
	{
		Shadow->SetTranslucentSortPriority(Brawler::SortShadow);
	}

	if (BlinkTimer > 0.f)
	{
		const bool bVisible = FMath::Fmod(BlinkTimer, 0.12f) > 0.06f;
		Sprite->SetVisibility(bVisible);
	}
	else if (!Sprite->IsVisible())
	{
		Sprite->SetVisibility(true);
	}
}
