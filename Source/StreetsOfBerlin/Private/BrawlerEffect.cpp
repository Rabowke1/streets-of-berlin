#include "BrawlerEffect.h"

ABrawlerEffect::ABrawlerEffect()
{
	ShadowScale = 0.f;
	SpriteFootOffset = 0.f;
}

void ABrawlerEffect::Init(const FString& InPrefix, float InFPS, float InScale, bool bInFront)
{
	Prefix = InPrefix;
	FPS = InFPS;
	SpriteScale = InScale;
	bUseDepthSort = !bInFront;
	FixedSortPriority = Brawler::SortEffects;
	SortOffset = 3;
	// Staubwolken sitzen auf dem Boden, Funken zentriert auf dem Trefferpunkt
	SpriteFootOffset = InPrefix.Contains(TEXT("Dust")) ? 30.f * InScale : 0.f;
}

void ABrawlerEffect::BeginPlay()
{
	Super::BeginPlay();
	PlayFrames(TEXT("Effects"), Prefix, FPS, false, true);
	if (CurrentFrames.Num() == 0)
	{
		Destroy();
	}
}

void ABrawlerEffect::TickEntity(float DeltaSeconds)
{
	if (IsAnimFinished())
	{
		Destroy();
	}
}
