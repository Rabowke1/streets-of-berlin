#include "BrawlerWeaponItem.h"

#include "BrawlerAssets.h"
#include "BrawlerFighter.h"
#include "BrawlerGameMode.h"
#include "BrawlerStageData.h"
#include "EngineUtils.h"
#include "PaperSprite.h"
#include "PaperSpriteComponent.h"
#include "Engine/World.h"

// ---------------------------------------------------------------------------
// Waffe am Boden
// ---------------------------------------------------------------------------
ABrawlerWeaponItem::ABrawlerWeaponItem()
{
	ShadowScale = 0.6f;
	SortOffset = -2;
}

void ABrawlerWeaponItem::Init(FName InType, int32 InDurability)
{
	Type = InType;
	Durability = InDurability;
}

void ABrawlerWeaponItem::BeginPlay()
{
	Super::BeginPlay();
	if (UBrawlerAssets* Assets = UBrawlerAssets::Get(this))
	{
		UPaperSprite* Spr = Assets->GetSprite(TEXT("Weapons"), TEXT("Weapon_") + Type.ToString());
		SetStaticSprite(Spr);
		if (Spr)
		{
			SpriteFootOffset = -Spr->GetRenderBounds().GetBox().Min.Z - 4.f;
		}
	}
}

void ABrawlerWeaponItem::Pop(float Direction)
{
	Height = FMath::Max(Height, 1.f);
	VelZ = 420.f;
	VelX = Direction * 120.f;
}

void ABrawlerWeaponItem::TickEntity(float DeltaSeconds)
{
	Life += DeltaSeconds;
	if (Height > 0.f || VelZ > 0.f)
	{
		VelZ -= Brawler::Gravity * DeltaSeconds;
		Height += VelZ * DeltaSeconds;
		PosX += VelX * DeltaSeconds;
		if (Height <= 0.f)
		{
			Height = 0.f;
			VelZ = 0.f;
			VelX = 0.f;
		}
	}
	// Liegengelassene Waffen verschwinden nach einer Weile
	if (Life > 18.f)
	{
		BlinkTimer = Life;
		if (Life > 20.f)
		{
			Destroy();
		}
	}
}

void ABrawlerWeaponItem::Collect(ABrawlerFighter* Fighter)
{
	if (bCollected || !Fighter)
	{
		return;
	}
	bCollected = true;
	Fighter->TakeWeapon(Type, Durability);
	if (ABrawlerGameMode* GM = GetWorld() ? Cast<ABrawlerGameMode>(GetWorld()->GetAuthGameMode()) : nullptr)
	{
		GM->PlaySfx(TEXT("SFX_Pickup"), 0.6f, 0.1f);
	}
	Destroy();
}

// ---------------------------------------------------------------------------
// Geworfene Waffe
// ---------------------------------------------------------------------------
ABrawlerProjectile::ABrawlerProjectile()
{
	ShadowScale = 0.5f;
	SpriteFootOffset = 0.f;
}

void ABrawlerProjectile::Init(FName InType, ABrawlerFighter* InOwner, float InDamage, int32 InDurability)
{
	Type = InType;
	Thrower = InOwner;
	Team = InOwner ? InOwner->Team : EBrawlerTeam::Player;
	Damage = InDamage;
	Durability = InDurability;
}

void ABrawlerProjectile::BeginPlay()
{
	Super::BeginPlay();
	if (UBrawlerAssets* Assets = UBrawlerAssets::Get(this))
	{
		SetStaticSprite(Assets->GetSprite(TEXT("Weapons"), TEXT("Weapon_") + Type.ToString()));
	}
	VelX = Facing * 900.f;
}

void ABrawlerProjectile::TickEntity(float DeltaSeconds)
{
	PosX += VelX * DeltaSeconds;
	Travel += FMath::Abs(VelX * DeltaSeconds);
	if (Type != FName(TEXT("Knife")))
	{
		Spin += DeltaSeconds * 1000.f;
		Sprite->SetRelativeRotation(FRotator(-Spin * Facing, 0.f, 0.f));
	}

	FBrawlerAttack Hit;
	Hit.Damage = Damage;
	Hit.HitType = EHitType::Knockdown;
	Hit.Knockback = 300.f;
	Hit.Launch = 420.f;
	Hit.Hitstop = 0.08f;

	ABrawlerFighter* Owner = Thrower.Get();
	for (TActorIterator<ABrawlerEntity> It(GetWorld()); It; ++It)
	{
		ABrawlerEntity* Target = *It;
		if (Target == this || Target == Owner || !IsValid(Target) || !Target->IsHittable(Team))
		{
			continue;
		}
		if (FMath::Abs(Target->PosX - PosX) > 40.f + Target->GetHurtHalfWidth() || FMath::Abs(Target->Depth - Depth) > 24.f)
		{
			continue;
		}
		if (Height - 20.f > Target->Height + Target->GetHurtHeight() || Height + 60.f < Target->Height)
		{
			continue;
		}
		if (Owner && Target->ReceiveHit(Owner, Hit, Facing))
		{
			Land(true);
			return;
		}
	}

	const ABrawlerGameMode* GM = GetWorld() ? Cast<ABrawlerGameMode>(GetWorld()->GetAuthGameMode()) : nullptr;
	if (Travel > 900.f || (GM && (PosX < GM->GetViewMinX() - 100.f || PosX > GM->GetViewMaxX() + 100.f)))
	{
		Land(false);
	}
}

void ABrawlerProjectile::Land(bool bHit)
{
	ABrawlerGameMode* GM = GetWorld() ? Cast<ABrawlerGameMode>(GetWorld()->GetAuthGameMode()) : nullptr;
	if (Type == FName(TEXT("Bottle")))
	{
		if (GM)
		{
			GM->SpawnEffect(TEXT("FX_HitSpark"), PosX, Depth, Height, Facing, 22.f);
			GM->PlaySfx(TEXT("SFX_Break"), 0.8f, 0.1f);
		}
	}
	else if (Durability > 1)
	{
		FActorSpawnParameters Params;
		Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
		Params.bDeferConstruction = true;
		if (ABrawlerWeaponItem* Item = GetWorld()->SpawnActor<ABrawlerWeaponItem>(ABrawlerWeaponItem::StaticClass(), FTransform::Identity, Params))
		{
			Item->Init(Type, Durability - 1);
			Item->SetBeltPosition(PosX, Depth, Height);
			Item->FinishSpawning(FTransform::Identity);
			Item->Pop(bHit ? -Facing : Facing * 0.5f);
		}
	}
	Destroy();
}
