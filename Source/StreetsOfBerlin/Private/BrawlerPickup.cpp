#include "BrawlerPickup.h"

#include "BrawlerAssets.h"
#include "BrawlerGameMode.h"
#include "BrawlerPlayer.h"
#include "PaperSprite.h"
#include "PaperSpriteComponent.h"
#include "Engine/World.h"

ABrawlerPickup::ABrawlerPickup()
{
	ShadowScale = 0.5f;
	SortOffset = -2;
}

void ABrawlerPickup::Init(FName InType)
{
	Type = InType;
}

void ABrawlerPickup::BeginPlay()
{
	Super::BeginPlay();
	if (UBrawlerAssets* Assets = UBrawlerAssets::Get(this))
	{
		UPaperSprite* Spr = Assets->GetSprite(TEXT("Props"), TEXT("Pickup_") + Type.ToString());
		SetStaticSprite(Spr);
		if (Spr)
		{
			// Unterkante des Bildes auf den Boden setzen
			SpriteFootOffset = -Spr->GetRenderBounds().GetBox().Min.Z - 4.f;
		}
	}
}

void ABrawlerPickup::Pop(float Direction)
{
	Height = 1.f;
	VelZ = 520.f;
	VelX = Direction * 110.f;
}

void ABrawlerPickup::TickEntity(float DeltaSeconds)
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
}

void ABrawlerPickup::Collect(ABrawlerPlayer* Player)
{
	if (bCollected || !Player)
	{
		return;
	}
	bCollected = true;

	ABrawlerGameMode* GM = GetWorld() ? Cast<ABrawlerGameMode>(GetWorld()->GetAuthGameMode()) : nullptr;
	if (Type == TEXT("Doener"))
	{
		Player->Heal(Player->MaxHealth);
		if (GM) GM->AddScore(200);
	}
	else if (Type == TEXT("Currywurst"))
	{
		Player->Heal(45.f);
		if (GM) GM->AddScore(100);
	}
	else if (Type == TEXT("Money"))
	{
		if (GM) GM->AddScore(1000);
	}

	if (GM)
	{
		GM->PlaySfx(TEXT("SFX_Pickup"), 0.9f, 0.f);
	}
	Destroy();
}
