#include "BrawlerProp.h"

#include "BrawlerAssets.h"
#include "BrawlerGameMode.h"
#include "BrawlerPickup.h"
#include "PaperSprite.h"
#include "Engine/World.h"

ABrawlerProp::ABrawlerProp()
{
	ShadowScale = 0.95f;
}

void ABrawlerProp::Init(FName InType, FName InDrop)
{
	Type = InType;
	Drop = InDrop;
}

void ABrawlerProp::BeginPlay()
{
	Super::BeginPlay();
	PlayFrames(TEXT("Props"), TEXT("Prop_") + Type.ToString(), 0.f, false, true);
	SetAnimFrame(0);
	if (CurrentFrames.Num() > 0 && CurrentFrames[0])
	{
		SpriteFootOffset = -CurrentFrames[0]->GetRenderBounds().GetBox().Min.Z - 5.f;
	}
}

bool ABrawlerProp::IsHittable(EBrawlerTeam AttackerTeam) const
{
	return !bBroken && AttackerTeam == EBrawlerTeam::Player;
}

bool ABrawlerProp::ReceiveHit(ABrawlerFighter* Attacker, const FBrawlerAttack& Attack, float Direction)
{
	if (bBroken)
	{
		return false;
	}

	ABrawlerGameMode* GM = GetWorld() ? Cast<ABrawlerGameMode>(GetWorld()->GetAuthGameMode()) : nullptr;
	--HitsLeft;
	AddHitstop(0.06f);
	if (GM)
	{
		GM->SpawnEffect(TEXT("FX_HitSpark"), PosX - Direction * 20.f, Depth, 70.f, Direction, 22.f);
	}

	if (HitsLeft > 0 && Attack.HitType == EHitType::Light)
	{
		if (GM) GM->PlaySfx(TEXT("SFX_HitLight"), 0.7f);
		return true;
	}

	bBroken = true;
	SetAnimFrame(1);
	if (GM)
	{
		GM->PlaySfx(TEXT("SFX_Break"), 0.9f);
		GM->AddScore(50);
		GM->SpawnEffect(TEXT("FX_Dust"), PosX, Depth, 0.f, Direction, 14.f);
	}

	if (!Drop.IsNone())
	{
		FActorSpawnParameters Params;
		Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
		Params.bDeferConstruction = true;
		if (ABrawlerPickup* Pickup = GetWorld()->SpawnActor<ABrawlerPickup>(ABrawlerPickup::StaticClass(), FTransform(Brawler::ToWorld(PosX, Depth, 0.f)), Params))
		{
			Pickup->Init(Drop);
			Pickup->SetBeltPosition(PosX, Depth - 2.f, 0.f);
			Pickup->FinishSpawning(FTransform(Brawler::ToWorld(PosX, Depth, 0.f)));
			Pickup->Pop(Direction);
		}
	}
	return true;
}

void ABrawlerProp::TickEntity(float DeltaSeconds)
{
	if (bBroken)
	{
		BrokenTime += DeltaSeconds;
		BlinkTimer = BrokenTime > 1.2f ? BrokenTime : 0.f;
		if (BrokenTime > 2.2f)
		{
			Destroy();
		}
	}
}
